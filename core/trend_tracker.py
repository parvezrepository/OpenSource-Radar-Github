"""Historical trend tracking and star velocity analysis engine."""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from config import get_settings
from database.connection import get_db
from database.models import Repository, RepositorySnapshot

logger = logging.getLogger("opensource_radar.trend_tracker")


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime object is timezone-aware UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class TrendTracker:
    """Computes verified historical growth rates from point-in-time snapshot observations."""

    def __init__(self, min_snapshot_interval_minutes: Optional[int] = None):
        settings = get_settings()
        self.min_interval_minutes = (
            min_snapshot_interval_minutes
            if min_snapshot_interval_minutes is not None
            else settings.SNAPSHOT_MIN_INTERVAL_MINUTES
        )

    def record_snapshot(
        self,
        repository_id: int,
        stars: int,
        forks: int,
        open_issues: int,
        force: bool = False,
        recorded_at: Optional[datetime] = None,
        session: Optional[Session] = None,
    ) -> Optional[RepositorySnapshot]:
        """Record a quantitative observation snapshot if outside the minimum throttle interval.
        
        Avoids recording duplicate observations within `min_interval_minutes`.
        """
        now = _to_utc(recorded_at) or datetime.now(timezone.utc)

        def _do_record(s: Session) -> Optional[RepositorySnapshot]:
            if not force:
                latest = s.execute(
                    select(RepositorySnapshot)
                    .where(RepositorySnapshot.repository_id == repository_id)
                    .order_by(desc(RepositorySnapshot.recorded_at))
                    .limit(1)
                ).scalars().first()

                if latest:
                    latest_utc = _to_utc(latest.recorded_at)
                    elapsed = (now - latest_utc).total_seconds()
                    if elapsed < (self.min_interval_minutes * 60):
                        logger.debug(
                            "Snapshot skipped for repo_id=%d: elapsed %ds < threshold %ds",
                            repository_id,
                            elapsed,
                            self.min_interval_minutes * 60,
                        )
                        return None

            snapshot = RepositorySnapshot(
                repository_id=repository_id,
                stars=stars,
                forks=forks,
                open_issues=open_issues,
                recorded_at=now,
            )
            s.add(snapshot)
            logger.info("Recorded snapshot for repo_id=%d: stars=%d forks=%d", repository_id, stars, forks)
            return snapshot

        if session is not None:
            return _do_record(session)
        else:
            with get_db() as s:
                return _do_record(s)

    def calculate_growth(
        self,
        repository_id: int,
        session: Optional[Session] = None,
    ) -> dict[str, Any]:
        """Calculate observed star growth across 24h, 7d, and 30d observation windows.
        
        Strict Data Integrity Non-Negotiable:
        - Never fabricates historical metrics.
        - Differentiates between insufficient data and genuine flat/zero growth.
        - Requires at least 2 snapshot observations over time.
        """
        def _compute(s: Session) -> dict[str, Any]:
            snapshots = list(s.execute(
                select(RepositorySnapshot)
                .where(RepositorySnapshot.repository_id == repository_id)
                .order_by(RepositorySnapshot.recorded_at.asc())
            ).scalars().all())

            total_snapshots = len(snapshots)

            if total_snapshots < 2:
                return {
                    "status": "insufficient_data",
                    "has_sufficient_data": False,
                    "message": "Insufficient historical data. Growth analysis requires at least 2 snapshot observations recorded over time.",
                    "total_snapshots": total_snapshots,
                    "first_observation": snapshots[0].recorded_at if total_snapshots == 1 else None,
                    "latest_observation": snapshots[0].recorded_at if total_snapshots == 1 else None,
                    "growth_24h": None,
                    "growth_7d": None,
                    "growth_30d": None,
                    "total_observed_growth": None,
                }

            latest = snapshots[-1]
            earliest = snapshots[0]
            latest_time = _to_utc(latest.recorded_at)
            earliest_time = _to_utc(earliest.recorded_at)

            def _find_window_growth(target_hours: int, min_hours: float, max_hours: float) -> dict[str, Any]:
                target_dt = latest_time - timedelta(hours=target_hours)
                
                # Filter candidates that fall within the permissible range
                candidates = []
                for snap in snapshots[:-1]:
                    snap_time = _to_utc(snap.recorded_at)
                    diff_hours = (latest_time - snap_time).total_seconds() / 3600.0
                    if min_hours <= diff_hours <= max_hours:
                        candidates.append((abs((snap_time - target_dt).total_seconds()), snap, diff_hours))

                if not candidates:
                    return {
                        "status": "insufficient_data",
                        "available": False,
                        "message": f"No baseline snapshot found within {target_hours}h window ({min_hours:.0f}h–{max_hours:.0f}h).",
                        "delta_stars": None,
                        "growth_percent": None,
                        "hours_elapsed": None,
                    }

                # Sort by closeness to target_dt
                candidates.sort(key=lambda x: x[0])
                _, baseline_snap, actual_hours = candidates[0]

                delta_stars = latest.stars - baseline_snap.stars
                pct = round((delta_stars / baseline_snap.stars * 100.0), 2) if baseline_snap.stars > 0 else 0.0

                return {
                    "status": "ok",
                    "available": True,
                    "delta_stars": delta_stars,
                    "growth_percent": pct,
                    "baseline_stars": baseline_snap.stars,
                    "current_stars": latest.stars,
                    "hours_elapsed": round(actual_hours, 1),
                    "baseline_recorded_at": baseline_snap.recorded_at,
                }

            # Windows: 24h (18h-36h), 7d (120h-216h), 30d (600h-900h)
            growth_24h = _find_window_growth(24, min_hours=18.0, max_hours=36.0)
            growth_7d = _find_window_growth(168, min_hours=120.0, max_hours=216.0)
            growth_30d = _find_window_growth(720, min_hours=600.0, max_hours=900.0)

            # Total observed growth between earliest recorded and latest
            total_delta_stars = latest.stars - earliest.stars
            total_pct = (
                round((total_delta_stars / earliest.stars * 100.0), 2)
                if earliest.stars > 0
                else 0.0
            )
            total_hours = round((latest_time - earliest_time).total_seconds() / 3600.0, 1)

            return {
                "status": "ok",
                "has_sufficient_data": True,
                "total_snapshots": total_snapshots,
                "first_observation": earliest.recorded_at,
                "latest_observation": latest.recorded_at,
                "growth_24h": growth_24h,
                "growth_7d": growth_7d,
                "growth_30d": growth_30d,
                "total_observed_growth": {
                    "status": "ok",
                    "delta_stars": total_delta_stars,
                    "growth_percent": total_pct,
                    "baseline_stars": earliest.stars,
                    "current_stars": latest.stars,
                    "hours_elapsed": total_hours,
                },
            }

        if session is not None:
            return _compute(session)
        else:
            with get_db() as s:
                return _compute(s)

    def get_time_series(self, repository_id: int) -> list[dict[str, Any]]:
        """Retrieve full chronological snapshot series formatted for charting."""
        with get_db() as session:
            snapshots = list(session.execute(
                select(RepositorySnapshot)
                .where(RepositorySnapshot.repository_id == repository_id)
                .order_by(RepositorySnapshot.recorded_at.asc())
            ).scalars().all())

            return [
                {
                    "recorded_at": s.recorded_at,
                    "stars": s.stars,
                    "forks": s.forks,
                    "open_issues": s.open_issues,
                }
                for s in snapshots
            ]

    def get_high_velocity_repositories(self, limit: int = 10) -> list[dict[str, Any]]:
        """Identify repositories with highest measured star velocity among observed snapshots."""
        with get_db() as session:
            repo_ids = list(session.execute(
                select(RepositorySnapshot.repository_id).distinct()
            ).scalars().all())

            scored = []
            for rid in repo_ids:
                growth_info = self.calculate_growth(rid, session=session)
                if not growth_info.get("has_sufficient_data"):
                    continue

                repo = session.execute(select(Repository).where(Repository.id == rid)).scalars().first()
                if not repo:
                    continue

                tot = growth_info["total_observed_growth"]
                scored.append({
                    "repository_id": rid,
                    "full_name": repo.full_name,
                    "current_stars": repo.stars,
                    "delta_stars": tot["delta_stars"],
                    "growth_percent": tot["growth_percent"],
                    "hours_elapsed": tot["hours_elapsed"],
                    "snapshots_count": growth_info["total_snapshots"],
                })

            scored.sort(key=lambda x: (x["delta_stars"], x["growth_percent"]), reverse=True)
            return scored[:limit]


# Global singleton
trend_tracker = TrendTracker()
