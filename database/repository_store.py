"""High-level repository data access object (DAO) for OpenSource Radar."""

from datetime import datetime, timezone
import logging
from typing import Any, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db
from database.models import (
    Category,
    ContentDraft,
    Repository,
    RepositoryAnalysis,
    RepositorySnapshot,
    SavedRepository,
    SearchHistory,
)

logger = logging.getLogger("opensource_radar.store")


def _parse_dt(val: Any) -> Optional[datetime]:
    """Safely parse ISO string or object to python datetime for SQLite."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            pass
        try:
            from dateutil import parser
            return parser.parse(val)
        except Exception:
            return None
    return None


class RepositoryStore:
    """Thread-safe persistence and query management for repositories."""

    @staticmethod
    def upsert_repository(repo_data: dict[str, Any], session: Optional[Session] = None) -> Repository:
        """Insert or update a repository record by its unique github_id."""
        def _do_upsert(s: Session) -> Repository:
            github_id = repo_data.get("github_id") or repo_data.get("id")
            if not github_id:
                raise ValueError("Repository data must contain 'github_id' or 'id'.")

            existing = s.execute(
                select(Repository).where(Repository.github_id == github_id)
            ).scalars().first()

            if existing:
                # Update volatile metrics
                existing.stars = repo_data.get("stars", existing.stars)
                existing.forks = repo_data.get("forks", existing.forks)
                existing.open_issues = repo_data.get("open_issues", existing.open_issues)
                existing.description = repo_data.get("description", existing.description)
                existing.pushed_at_github = _parse_dt(repo_data.get("pushed_at_github") or repo_data.get("pushed_at")) or existing.pushed_at_github
                existing.updated_at_github = _parse_dt(repo_data.get("updated_at_github") or repo_data.get("updated_at")) or existing.updated_at_github
                existing.created_at_github = _parse_dt(repo_data.get("created_at_github") or repo_data.get("created_at")) or existing.created_at_github
                existing.topics = repo_data.get("topics", existing.topics)
                existing.last_scraped_at = datetime.now(timezone.utc)
                if repo_data.get("category_id") is not None:
                    existing.category_id = repo_data["category_id"]
                repo = existing
            else:
                full_name = repo_data.get("full_name") or f"{repo_data.get('owner', '')}/{repo_data.get('name', '')}"
                owner = repo_data.get("owner") or (full_name.split("/")[0] if "/" in full_name else "")
                name = repo_data.get("name") or (full_name.split("/")[1] if "/" in full_name else "")
                html_url = repo_data.get("html_url") or f"https://github.com/{full_name}"

                repo = Repository(
                    github_id=github_id,
                    full_name=full_name,
                    owner=owner,
                    name=name,
                    html_url=html_url,
                    description=repo_data.get("description"),
                    stars=repo_data.get("stars", 0),
                    forks=repo_data.get("forks", 0),
                    open_issues=repo_data.get("open_issues", 0),
                    repo_size_kb=repo_data.get("repo_size_kb", 0),
                    primary_language=repo_data.get("primary_language"),
                    topics=repo_data.get("topics", []),
                    license_key=repo_data.get("license_key"),
                    license_name=repo_data.get("license_name") or repo_data.get("license"),
                    default_branch=repo_data.get("default_branch", "main"),
                    is_archived=repo_data.get("is_archived", False),
                    created_at_github=_parse_dt(repo_data.get("created_at_github") or repo_data.get("created_at")),
                    updated_at_github=_parse_dt(repo_data.get("updated_at_github") or repo_data.get("updated_at")),
                    pushed_at_github=_parse_dt(repo_data.get("pushed_at_github") or repo_data.get("pushed_at")),
                    category_id=repo_data.get("category_id"),
                    last_scraped_at=datetime.now(timezone.utc),
                )
                s.add(repo)

            return repo

        if session is not None:
            return _do_upsert(session)
        else:
            with get_db() as s:
                return _do_upsert(s)

    @staticmethod
    def get_by_github_id(github_id: int) -> Optional[Repository]:
        """Retrieve repository by GitHub ID."""
        with get_db() as session:
            return session.execute(
                select(Repository).where(Repository.github_id == github_id)
            ).scalars().first()

    @staticmethod
    def get_by_full_name(full_name: str) -> Optional[Repository]:
        """Retrieve repository by 'owner/repo' name."""
        with get_db() as session:
            return session.execute(
                select(Repository)
                .options(joinedload(Repository.category), joinedload(Repository.analyses))
                .where(Repository.full_name == full_name.strip())
            ).scalars().first()

    @staticmethod
    def list_repositories(
        category_key: Optional[str] = None,
        min_stars: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Repository]:
        """List repositories with optional category filtering and pagination."""
        with get_db() as session:
            stmt = select(Repository).options(joinedload(Repository.category))
            if category_key:
                stmt = stmt.join(Repository.category).where(Category.key == category_key)
            if min_stars > 0:
                stmt = stmt.where(Repository.stars >= min_stars)
            stmt = stmt.order_by(desc(Repository.stars)).offset(offset).limit(limit)
            return list(session.execute(stmt).scalars().all())

    @staticmethod
    def save_repository(repo_id: int, notes: str = "", tags: Optional[list[str]] = None) -> bool:
        """Bookmark a repository."""
        tags = tags or []
        with get_db() as session:
            existing = session.execute(
                select(SavedRepository).where(SavedRepository.repository_id == repo_id)
            ).scalars().first()
            if existing:
                existing.notes = notes
                existing.tags = tags
            else:
                bookmark = SavedRepository(
                    repository_id=repo_id,
                    notes=notes,
                    tags=tags,
                )
                session.add(bookmark)
            return True

    @staticmethod
    def unsave_repository(repo_id: int) -> bool:
        """Remove a bookmark."""
        with get_db() as session:
            existing = session.execute(
                select(SavedRepository).where(SavedRepository.repository_id == repo_id)
            ).scalars().first()
            if existing:
                session.delete(existing)
                return True
            return False

    @staticmethod
    def is_saved(repo_id: int) -> bool:
        """Check if repository is bookmarked."""
        with get_db() as session:
            count = session.execute(
                select(func.count(SavedRepository.id)).where(SavedRepository.repository_id == repo_id)
            ).scalar() or 0
            return count > 0

    @staticmethod
    def list_saved_repositories() -> list[dict[str, Any]]:
        """List all bookmarked repositories with related details."""
        with get_db() as session:
            stmt = (
                select(SavedRepository)
                .options(joinedload(SavedRepository.repository).joinedload(Repository.category))
                .order_by(desc(SavedRepository.saved_at))
            )
            saved_list = session.execute(stmt).scalars().all()
            results = []
            for item in saved_list:
                results.append({
                    "saved_id": item.id,
                    "repository_id": item.repository_id,
                    "notes": item.notes,
                    "tags": item.tags,
                    "saved_at": item.saved_at,
                    "repository": item.repository,
                })
            return results

    @staticmethod
    def get_overview_stats() -> dict[str, Any]:
        """Retrieve aggregated database statistics for the Overview dashboard."""
        with get_db() as session:
            total_discovered = session.execute(select(func.count(Repository.id))).scalar() or 0
            total_saved = session.execute(select(func.count(SavedRepository.id))).scalar() or 0
            total_analyzed = session.execute(select(func.count(RepositoryAnalysis.id))).scalar() or 0
            total_drafts = session.execute(select(func.count(ContentDraft.id))).scalar() or 0
            total_snapshots = session.execute(select(func.count(RepositorySnapshot.id))).scalar() or 0

            # Recent 5 discoveries
            recent_repos = list(session.execute(
                select(Repository)
                .options(joinedload(Repository.category))
                .order_by(desc(Repository.last_scraped_at))
                .limit(5)
            ).scalars().all())

            return {
                "total_discovered": total_discovered,
                "total_saved": total_saved,
                "total_analyzed": total_analyzed,
                "total_drafts": total_drafts,
                "total_snapshots": total_snapshots,
                "recent_repositories": recent_repos,
            }

    @staticmethod
    def get_snapshots_count() -> int:
        """Return total number of point-in-time snapshots."""
        with get_db() as session:
            return session.execute(select(func.count(RepositorySnapshot.id))).scalar() or 0

    @staticmethod
    def get_snapshots(repository_id: int, limit: int = 100) -> list[RepositorySnapshot]:
        """Retrieve chronological snapshots for a repository."""
        with get_db() as session:
            return list(session.execute(
                select(RepositorySnapshot)
                .where(RepositorySnapshot.repository_id == repository_id)
                .order_by(RepositorySnapshot.recorded_at.asc())
                .limit(limit)
            ).scalars().all())

    @staticmethod
    def get_repositories_with_snapshots() -> list[Repository]:
        """Retrieve all repositories that have at least one snapshot recorded."""
        with get_db() as session:
            repo_ids_with_snapshots = select(RepositorySnapshot.repository_id).distinct()
            return list(session.execute(
                select(Repository)
                .options(joinedload(Repository.category))
                .where(Repository.id.in_(repo_ids_with_snapshots))
                .order_by(Repository.full_name.asc())
            ).scalars().all())

    @staticmethod
    def get_category_distribution() -> dict[str, int]:
        """Get repository count grouped by category display name."""
        with get_db() as session:
            results = session.execute(
                select(Category.display_name, func.count(Repository.id))
                .join(Repository.category)
                .group_by(Category.display_name)
            ).all()
            return {row[0]: row[1] for row in results}

    @staticmethod
    def get_language_distribution(limit: int = 10) -> dict[str, int]:
        """Get repository count grouped by primary programming language."""
        with get_db() as session:
            results = session.execute(
                select(Repository.primary_language, func.count(Repository.id))
                .where(Repository.primary_language.isnot(None))
                .group_by(Repository.primary_language)
                .order_by(desc(func.count(Repository.id)))
                .limit(limit)
            ).all()
            return {row[0]: row[1] for row in results}

    @staticmethod
    def log_search(query_string: str, filters: dict[str, Any], result_count: int) -> None:
        """Record search history."""
        with get_db() as session:
            entry = SearchHistory(
                query_string=query_string,
                filters_applied=filters,
                result_count=result_count,
            )
            session.add(entry)

    @staticmethod
    def get_recent_searches(limit: int = 10) -> list[SearchHistory]:
        """Retrieve recent search queries."""
        with get_db() as session:
            return list(session.execute(
                select(SearchHistory).order_by(desc(SearchHistory.executed_at)).limit(limit)
            ).scalars().all())
