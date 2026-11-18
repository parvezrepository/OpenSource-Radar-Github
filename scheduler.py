"""OpenSource Radar — Standalone Background Scheduler Process.

Runs autonomous discovery jobs and historical snapshot capture on configured intervals.
Uses APScheduler in an isolated process to prevent thread leaks and database locks.
"""

import argparse
import atexit
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import signal
import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import BASE_DIR, get_settings
from database.connection import init_db
from database.models import DiscoveryJob
from services.monitoring_service import NotificationEvent, monitoring_service
from services.scheduler_service import scheduler_service

# Logging setup for standalone scheduler
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PID_FILE = LOGS_DIR / "scheduler.pid"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "scheduler.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("opensource_radar.scheduler")


def is_pid_running(pid: int) -> bool:
    """Check if a process with given PID is currently active."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def acquire_pid_lock() -> bool:
    """Acquire single-instance process lock. Return True if successful."""
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            if is_pid_running(old_pid):
                logger.warning(
                    "Scheduler process already active with PID %d. Exiting to prevent duplicate instances.",
                    old_pid,
                )
                return False
            else:
                logger.info("Removing stale PID file from inactive process %d.", old_pid)
                PID_FILE.unlink(missing_ok=True)
        except Exception as e:
            logger.warning("Could not read existing PID file: %s. Overwriting.", str(e))
            PID_FILE.unlink(missing_ok=True)

    current_pid = os.getpid()
    PID_FILE.write_text(str(current_pid), encoding="utf-8")
    logger.info("Acquired scheduler PID lock: %d", current_pid)
    return True


def release_pid_lock() -> None:
    """Remove PID lockfile upon clean exit."""
    if PID_FILE.exists():
        try:
            stored_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            if stored_pid == os.getpid():
                PID_FILE.unlink(missing_ok=True)
                logger.info("Released scheduler PID lock: %d", stored_pid)
        except Exception:
            PID_FILE.unlink(missing_ok=True)


class RadarScheduler:
    """Standalone APScheduler runner executing configured discovery jobs."""

    def __init__(self):
        self.scheduler = BlockingScheduler()
        self._running = False

    def schedule_jobs(self) -> int:
        """Register all enabled database jobs with APScheduler."""
        jobs = scheduler_service.list_jobs()
        registered = 0

        # Clear any existing scheduled jobs
        self.scheduler.remove_all_jobs()

        for j in jobs:
            if not j["is_enabled"]:
                continue

            job_id = j["id"]
            cron_expr = j["cron_expression"].strip()

            try:
                trigger = CronTrigger.from_crontab(cron_expr)
                self.scheduler.add_job(
                    func=scheduler_service.execute_job,
                    trigger=trigger,
                    args=[job_id],
                    id=f"job_{job_id}",
                    name=j["job_name"],
                    replace_existing=True,
                    misfire_grace_time=300,
                )
                registered += 1
                logger.info("Scheduled '%s' (ID %d) with cron '%s'", j["job_name"], job_id, cron_expr)
            except Exception as exc:
                logger.error("Failed to parse cron '%s' for job ID %d: %s", cron_expr, job_id, str(exc))

        # Add periodic sync job to refresh job definitions from DB every 5 minutes
        self.scheduler.add_job(
            func=self.refresh_jobs,
            trigger="interval",
            minutes=5,
            id="scheduler_sync",
            name="Job Definitions Sync",
            replace_existing=True,
        )

        return registered

    def refresh_jobs(self) -> None:
        """Periodic sync to load newly created or updated jobs from database."""
        logger.debug("Refreshing scheduled jobs from database...")
        self.schedule_jobs()

    def run(self) -> None:
        """Start the blocking scheduler event loop."""
        init_db()
        count = self.schedule_jobs()
        logger.info("OpenSource Radar Scheduler initialized with %d active jobs.", count)
        monitoring_service.notify(
            event_type=NotificationEvent.NEW_DISCOVERY,
            title="Scheduler Started",
            message=f"OpenSource Radar background daemon started with {count} active jobs.",
        )

        self._running = True
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler received interrupt signal. Shutting down gracefully...")
        except Exception as exc:
            logger.critical("Scheduler crashed unexpectedly: %s", str(exc), exc_info=True)
            monitoring_service.notify(
                event_type=NotificationEvent.SCHEDULER_FAILURE,
                title="Scheduler Daemon Failure",
                message=f"Critical daemon error: {str(exc)}",
            )
        finally:
            self._running = False
            release_pid_lock()


def handle_signals(signum, frame):
    """Handle termination signals."""
    logger.info("Received signal %d. Initiating graceful shutdown.", signum)
    release_pid_lock()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="OpenSource Radar Background Scheduler")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run all enabled jobs once sequentially and exit immediately (useful for testing).",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check whether the scheduler background daemon is currently running.",
    )
    args = parser.parse_args()

    # Status check mode
    if args.status:
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text(encoding="utf-8").strip())
                if is_pid_running(pid):
                    print(f"RUNNING: Scheduler is active with PID {pid}.")
                    sys.exit(0)
                else:
                    print(f"STOPPED: Stale PID file found ({pid}), but process is not running.")
                    sys.exit(1)
            except Exception:
                print("STOPPED: Error reading PID file.")
                sys.exit(1)
        else:
            print("STOPPED: Scheduler daemon is not running.")
            sys.exit(1)

    # Run once mode (for tests and verification)
    if args.once:
        print("Running all enabled discovery jobs once...")
        init_db()
        results = scheduler_service.run_all_enabled_jobs()
        print(f"Executed {len(results)} jobs.")
        for r in results:
            print(f" - [{r['status']}] {r['job_name']}: Discovered={r['discovered_count']}, Updated={r['updated_count']}")
        sys.exit(0)

    # Standard continuous daemon mode
    if not acquire_pid_lock():
        sys.exit(1)

    atexit.register(release_pid_lock)
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)

    daemon = RadarScheduler()
    daemon.run()


if __name__ == "__main__":
    main()
