"""Unit and integration tests for background scheduler service and monitoring alerts."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest

from core.github_client import GitHubRateLimitError
from database.connection import init_db
from database.models import DiscoveryJob, DiscoveryLog
from scheduler import acquire_pid_lock, is_pid_running, release_pid_lock
from services.monitoring_service import NotificationEvent, MonitoringService, monitoring_service
from services.scheduler_service import SchedulerService, scheduler_service


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema is initialized for tests."""
    init_db()


def test_seed_default_discovery_jobs():
    """Verify predefined default jobs are seeded on scheduler service initialization."""
    jobs = scheduler_service.list_jobs()
    assert len(jobs) >= 4

    job_names = [j["job_name"] for j in jobs]
    assert any("AI Projects" in name for name in job_names)
    assert any("Agents" in name for name in job_names)
    assert any("Trading" in name for name in job_names)
    assert any("Snapshot" in name for name in job_names)


def test_job_crud_and_toggle_lifecycle():
    """Verify creating, listing, toggling, and deleting discovery jobs."""
    service = SchedulerService()

    # Create new custom job
    new_job = service.create_or_update_job(
        job_name="Test Custom Job Alpha",
        category="security",
        query_params={"mode": "trending", "keywords": "osint"},
        cron_expression="0 3 * * *",
        is_enabled=True,
    )
    assert new_job.id is not None
    assert new_job.category == "security"

    # Toggle to disabled
    success_toggle = service.toggle_job(new_job.id, False)
    assert success_toggle is True

    jobs = service.list_jobs()
    matching = next((j for j in jobs if j["id"] == new_job.id), None)
    assert matching is not None
    assert matching["is_enabled"] is False

    # Delete
    deleted = service.delete_job(new_job.id)
    assert deleted is True

    jobs_after = service.list_jobs()
    assert not any(j["id"] == new_job.id for j in jobs_after)


def test_snapshot_job_execution():
    """Verify execution of a snapshot collection job."""
    service = SchedulerService()
    jobs = service.list_jobs()
    snap_job = next((j for j in jobs if j["category"] == "all" or "Snapshot" in j["job_name"]), jobs[0])

    result = service.execute_job(snap_job["id"])
    assert result["status"] == "SUCCESS"
    assert result["job_id"] == snap_job["id"]
    assert result["started_at"] is not None
    assert result["finished_at"] is not None

    logs = service.list_recent_logs(limit=5)
    assert any(l["id"] == result["log_id"] for l in logs)


def test_rate_limit_handling_in_discovery_job():
    """Verify scheduler handles GitHub API rate limits defensively and marks log as RATE_LIMITED."""
    service = SchedulerService()
    jobs = service.list_jobs()
    target_job = jobs[0]

    with patch("services.scheduler_service.discovery_engine.discover") as mock_discover:
        mock_discover.side_effect = GitHubRateLimitError("Rate limit reached. Reset in 1800s.", status_code=403)
        res = service.execute_job(target_job["id"])

        assert res["status"] == "RATE_LIMITED"
        assert "rate limit" in res["error_message"].lower()


def test_monitoring_service_dispatch_and_history():
    """Verify notification broadcasting and history logging without requiring external credentials."""
    mon = MonitoringService()

    alert = mon.notify(
        event_type=NotificationEvent.HIGH_POTENTIAL,
        title="High-Velocity Test Repo",
        message="Test alert description",
        metadata={"url": "https://github.com/test/repo"},
    )

    assert alert["event_type"] == NotificationEvent.HIGH_POTENTIAL
    assert alert["dispatched"]["LogNotificationProvider"] is True
    # Telegram is False when unconfigured, which is safe and non-blocking
    assert isinstance(alert["dispatched"].get("TelegramNotificationProvider"), bool)

    history = mon.get_recent_alerts(limit=5)
    assert len(history) > 0
    assert history[0]["title"] == "High-Velocity Test Repo"


def test_pid_running_check_and_lock_management():
    """Verify PID status detection and single-instance lock file behavior."""
    import os
    current_pid = os.getpid()

    assert is_pid_running(current_pid) is True
    assert is_pid_running(999999) is False

    # Acquire and release lock
    lock_acquired = acquire_pid_lock()
    assert lock_acquired is True

    # Releasing
    release_pid_lock()
