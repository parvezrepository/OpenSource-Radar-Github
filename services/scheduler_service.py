"""Scheduler service managing automated discovery jobs and background executions."""

from datetime import datetime, timezone
import logging
from typing import Any, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import joinedload

from core.discovery_engine import discovery_engine
from core.github_client import GitHubAPIError, GitHubClient, GitHubRateLimitError, get_github_client
from core.trend_tracker import trend_tracker
from database.connection import get_db
from database.models import DiscoveryJob, DiscoveryLog, Repository, SavedRepository
from database.repository_store import RepositoryStore
from services.monitoring_service import NotificationEvent, monitoring_service

logger = logging.getLogger("opensource_radar.scheduler_service")


class SchedulerService:
    """Manages recurring discovery jobs and execution logs."""

    def __init__(self):
        self.seed_default_jobs()

    def seed_default_jobs(self) -> None:
        """Seed predefined standard discovery jobs if table is empty."""
        defaults = [
            {
                "job_name": "AI Projects Daily Radar",
                "category": "ai",
                "query_params": {
                    "mode": "trending",
                    "category": "ai",
                    "keywords": "llm, artificial intelligence, deep learning",
                    "days_window": 3,
                    "per_page": 20,
                },
                "cron_expression": "0 0 * * *",
                "is_enabled": True,
            },
            {
                "job_name": "AI Agents 6-Hour Radar",
                "category": "agents",
                "query_params": {
                    "mode": "ai_agents",
                    "category": "agents",
                    "keywords": "ai-agents, mcp, autonomous-agents",
                    "days_window": 7,
                    "per_page": 20,
                },
                "cron_expression": "0 */6 * * *",
                "is_enabled": True,
            },
            {
                "job_name": "Trading & FinTech Daily Monitor",
                "category": "fintech",
                "query_params": {
                    "mode": "trading_fintech",
                    "category": "fintech",
                    "keywords": "algorithmic-trading, quantitative-finance, crypto-bot",
                    "days_window": 7,
                    "per_page": 20,
                },
                "cron_expression": "0 12 * * *",
                "is_enabled": True,
            },
            {
                "job_name": "Repository Historical Snapshot Collector",
                "category": "all",
                "query_params": {
                    "mode": "snapshots",
                    "limit": 50,
                },
                "cron_expression": "0 */6 * * *",
                "is_enabled": True,
            },
        ]

        with get_db() as session:
            count = session.execute(select(DiscoveryJob.id)).scalars().first()
            if count is None:
                for d in defaults:
                    job = DiscoveryJob(
                        job_name=d["job_name"],
                        category=d["category"],
                        query_params=d["query_params"],
                        cron_expression=d["cron_expression"],
                        is_enabled=d["is_enabled"],
                    )
                    session.add(job)
                logger.info("Seeded %d default discovery jobs.", len(defaults))

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all configured discovery jobs with latest execution status."""
        with get_db() as session:
            jobs = list(session.execute(
                select(DiscoveryJob).order_by(DiscoveryJob.created_at.asc())
            ).scalars().all())

            results = []
            for j in jobs:
                latest_log = session.execute(
                    select(DiscoveryLog)
                    .where(DiscoveryLog.job_id == j.id)
                    .order_by(desc(DiscoveryLog.started_at))
                    .limit(1)
                ).scalars().first()

                results.append({
                    "id": j.id,
                    "job_name": j.job_name,
                    "category": j.category,
                    "query_params": j.query_params,
                    "cron_expression": j.cron_expression,
                    "is_enabled": j.is_enabled,
                    "last_run_at": j.last_run_at,
                    "next_run_at": j.next_run_at,
                    "latest_status": latest_log.status if latest_log else "NEVER_RUN",
                    "latest_error": latest_log.error_message if latest_log else None,
                })
            return results

    def create_or_update_job(
        self,
        job_name: str,
        category: str,
        query_params: dict[str, Any],
        cron_expression: str,
        is_enabled: bool = True,
        job_id: Optional[int] = None,
    ) -> DiscoveryJob:
        """Create a new job definition or update an existing one."""
        with get_db() as session:
            if job_id:
                job = session.execute(
                    select(DiscoveryJob).where(DiscoveryJob.id == job_id)
                ).scalars().first()
                if not job:
                    raise ValueError(f"Job with id {job_id} not found.")
            else:
                job = session.execute(
                    select(DiscoveryJob).where(DiscoveryJob.job_name == job_name)
                ).scalars().first()

            if job:
                job.job_name = job_name
                job.category = category
                job.query_params = query_params
                job.cron_expression = cron_expression
                job.is_enabled = is_enabled
            else:
                job = DiscoveryJob(
                    job_name=job_name,
                    category=category,
                    query_params=query_params,
                    cron_expression=cron_expression,
                    is_enabled=is_enabled,
                )
                session.add(job)
            return job

    def toggle_job(self, job_id: int, is_enabled: bool) -> bool:
        """Enable or disable a scheduled job."""
        with get_db() as session:
            job = session.execute(
                select(DiscoveryJob).where(DiscoveryJob.id == job_id)
            ).scalars().first()
            if job:
                job.is_enabled = is_enabled
                return True
            return False

    def delete_job(self, job_id: int) -> bool:
        """Delete a discovery job and its associated logs."""
        with get_db() as session:
            job = session.execute(
                select(DiscoveryJob).where(DiscoveryJob.id == job_id)
            ).scalars().first()
            if job:
                session.delete(job)
                return True
            return False

    def execute_job(self, job_id: int) -> dict[str, Any]:
        """Execute a discovery or snapshot job, logging results to DiscoveryLog.
        
        Handles API errors, rate limits, and dispatches notifications on anomalies.
        """
        now = datetime.now(timezone.utc)
        with get_db() as session:
            job = session.execute(
                select(DiscoveryJob).where(DiscoveryJob.id == job_id)
            ).scalars().first()
            if not job:
                raise ValueError(f"Job id {job_id} not found.")

            log_entry = DiscoveryLog(
                job_id=job.id,
                started_at=now,
                status="RUNNING",
            )
            session.add(log_entry)
            session.flush()
            log_id = log_entry.id

        params = job.query_params or {}
        mode = params.get("mode", "trending")
        discovered_count = 0
        updated_count = 0
        error_msg = None
        status = "SUCCESS"

        try:
            if mode == "snapshots":
                # Collect snapshots for tracked repositories
                with get_db() as session:
                    repos = list(session.execute(
                        select(Repository).order_by(desc(Repository.stars)).limit(params.get("limit", 50))
                    ).scalars().all())

                for r in repos:
                    snap = trend_tracker.record_snapshot(
                        repository_id=r.id,
                        stars=r.stars,
                        forks=r.forks,
                        open_issues=r.open_issues,
                        force=False,
                    )
                    if snap:
                        discovered_count += 1
                updated_count = len(repos)
            else:
                # Run standard discovery search
                result = discovery_engine.discover(
                    mode=mode,
                    category=params.get("category", job.category if job.category != "all" else None),
                    language=params.get("language"),
                    custom_keywords=params.get("keywords"),
                    days_window=params.get("days_window", 7),
                    page=1,
                    per_page=params.get("per_page", 20),
                    persist=True,
                )
                items = result.get("items", [])
                discovered_count = len(items)
                updated_count = result.get("persisted_count", 0)

                # Record snapshot for discovered repos
                for item in items:
                    repo_rec = RepositoryStore.get_by_github_id(item["github_id"])
                    if repo_rec:
                        trend_tracker.record_snapshot(
                            repository_id=repo_rec.id,
                            stars=repo_rec.stars,
                            forks=repo_rec.forks,
                            open_issues=repo_rec.open_issues,
                            force=False,
                        )

                        # High potential alert trigger (e.g. >= 1000 stars or high traction)
                        if repo_rec.stars >= 1000:
                            monitoring_service.notify(
                                event_type=NotificationEvent.HIGH_POTENTIAL,
                                title=f"High-Potential Project: {repo_rec.full_name}",
                                message=f"Discovered by '{job.job_name}' with {repo_rec.stars:,} stars: {repo_rec.description or 'No description'}",
                                metadata={"url": repo_rec.html_url, "stars": repo_rec.stars},
                            )

        except GitHubRateLimitError as rle:
            status = "RATE_LIMITED"
            error_msg = f"GitHub API Rate Limit: {str(rle)}"
            logger.warning("Job %s hit rate limit: %s", job.job_name, error_msg)
            monitoring_service.notify(
                event_type=NotificationEvent.MONITORING_FAILURE,
                title=f"Rate Limit: {job.job_name}",
                message=error_msg,
            )
        except GitHubAPIError as gae:
            status = "FAILED"
            error_msg = f"GitHub API Error: {str(gae)}"
            logger.error("Job %s failed: %s", job.job_name, error_msg)
            monitoring_service.notify(
                event_type=NotificationEvent.MONITORING_FAILURE,
                title=f"API Failure: {job.job_name}",
                message=error_msg,
            )
        except Exception as exc:
            status = "FAILED"
            error_msg = f"Unexpected failure: {str(exc)}"
            logger.error("Job %s encountered unexpected exception: %s", job.job_name, error_msg)
            monitoring_service.notify(
                event_type=NotificationEvent.MONITORING_FAILURE,
                title=f"Job Failure: {job.job_name}",
                message=error_msg,
            )

        # Update log and job in database
        finished_at = datetime.now(timezone.utc)
        with get_db() as session:
            log_record = session.execute(
                select(DiscoveryLog).where(DiscoveryLog.id == log_id)
            ).scalars().first()
            if log_record:
                log_record.finished_at = finished_at
                log_record.discovered_count = discovered_count
                log_record.updated_count = updated_count
                log_record.status = status
                log_record.error_message = error_msg

            job_record = session.execute(
                select(DiscoveryJob).where(DiscoveryJob.id == job_id)
            ).scalars().first()
            if job_record:
                job_record.last_run_at = finished_at

        return {
            "log_id": log_id,
            "job_id": job_id,
            "job_name": job.job_name,
            "status": status,
            "discovered_count": discovered_count,
            "updated_count": updated_count,
            "started_at": now,
            "finished_at": finished_at,
            "error_message": error_msg,
        }

    def run_all_enabled_jobs(self) -> list[dict[str, Any]]:
        """Sequential execution of all enabled jobs."""
        with get_db() as session:
            enabled_ids = list(session.execute(
                select(DiscoveryJob.id).where(DiscoveryJob.is_enabled == True)
            ).scalars().all())

        results = []
        for jid in enabled_ids:
            try:
                res = self.execute_job(jid)
                results.append(res)
            except Exception as e:
                logger.error("Failed executing job %d: %s", jid, str(e))
        return results

    def list_recent_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve recent job execution logs."""
        with get_db() as session:
            logs = list(session.execute(
                select(DiscoveryLog)
                .options(joinedload(DiscoveryLog.job))
                .order_by(desc(DiscoveryLog.started_at))
                .limit(limit)
            ).scalars().all())

            return [
                {
                    "id": l.id,
                    "job_name": l.job.job_name if l.job else "Unknown",
                    "started_at": l.started_at,
                    "finished_at": l.finished_at,
                    "discovered_count": l.discovered_count,
                    "updated_count": l.updated_count,
                    "status": l.status,
                    "error_message": l.error_message,
                }
                for l in logs
            ]


# Global singleton
scheduler_service = SchedulerService()
