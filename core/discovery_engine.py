"""Global GitHub Technology Discovery Engine for OpenSource Radar."""

from datetime import datetime, timezone
import logging
from typing import Any, Optional
from sqlalchemy import select

from core.categorizer import categorizer
from core.github_client import GitHubAPIError, GitHubClient, get_github_client
from core.search_engine import DiscoveryMode, SearchEngine
from database.connection import get_db
from database.models import Category, Repository
from database.repository_store import RepositoryStore

logger = logging.getLogger("opensource_radar.discovery")


class DiscoveryEngine:
    """Orchestrates repository search, normalization, categorization, and persistence."""

    def __init__(self, github_client: Optional[GitHubClient] = None) -> None:
        self.client = github_client or get_github_client()

    @staticmethod
    def _parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
        """Safely parse GitHub ISO 8601 timestamp string into datetime."""
        if not date_str:
            return None
        try:
            # Handle standard '2026-11-17T12:00:00Z'
            clean_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(clean_str)
        except ValueError:
            return None

    def normalize_repository_data(self, raw_item: dict[str, Any]) -> dict[str, Any]:
        """
        Extract and normalize the 16 core fields required by OpenSource Radar.
        """
        owner_obj = raw_item.get("owner", {})
        license_obj = raw_item.get("license") or {}

        topics = raw_item.get("topics") or []
        description = raw_item.get("description")
        name = raw_item.get("name", "")

        # Categorize
        cat_key, subcategory, confidence = categorizer.classify_repository(
            topics=topics,
            description=description,
            name=name,
        )

        # Lookup category_id in DB if available
        category_id = None
        with get_db() as session:
            cat_db = session.execute(
                select(Category).where(Category.key == cat_key)
            ).scalars().first()
            if cat_db:
                category_id = cat_db.id

        return {
            "github_id": raw_item.get("id"),
            "full_name": raw_item.get("full_name"),
            "owner": owner_obj.get("login") or raw_item.get("full_name", "").split("/")[0],
            "name": name,
            "html_url": raw_item.get("html_url"),
            "description": description,
            "stars": raw_item.get("stargazers_count", 0),
            "forks": raw_item.get("forks_count", 0),
            "open_issues": raw_item.get("open_issues_count", 0),
            "repo_size_kb": raw_item.get("size", 0),
            "primary_language": raw_item.get("language"),
            "topics": topics,
            "license_key": license_obj.get("spdx_id") or license_obj.get("key"),
            "license_name": license_obj.get("name"),
            "default_branch": raw_item.get("default_branch", "main"),
            "is_archived": raw_item.get("archived", False),
            "created_at_github": self._parse_iso_date(raw_item.get("created_at")),
            "updated_at_github": self._parse_iso_date(raw_item.get("updated_at")),
            "pushed_at_github": self._parse_iso_date(raw_item.get("pushed_at")),
            "category_id": category_id,
            "category_key": cat_key,
            "subcategory": subcategory,
            "category_confidence": confidence,
        }

    def discover(
        self,
        mode: DiscoveryMode = "trending",
        category: Optional[str] = None,
        language: Optional[str] = None,
        custom_keywords: Optional[str] = None,
        days_window: int = 7,
        page: int = 1,
        per_page: int = 30,
        persist: bool = True,
    ) -> dict[str, Any]:
        """
        Execute discovery across one of the 9 discovery modes and persist results.
        """
        query, sort, order = SearchEngine.build_mode_query(
            mode=mode,
            category=category,
            language=language,
            custom_keywords=custom_keywords,
            days_window=days_window,
        )

        logger.info(f"Executing discovery mode='{mode}' query='{query}' sort='{sort}' order='{order}' page={page}")

        try:
            raw_response = self.client.search_repositories(
                query=query,
                sort=sort,
                order=order,
                page=page,
                per_page=per_page,
            )
        except GitHubAPIError as exc:
            logger.error(f"Discovery search failed: {exc}")
            raise

        raw_items = raw_response.get("items", [])
        total_count = raw_response.get("total_count", 0)

        normalized_repos = []
        persisted_repos = []

        for item in raw_items:
            norm = self.normalize_repository_data(item)
            normalized_repos.append(norm)

            if persist:
                try:
                    repo_record = RepositoryStore.upsert_repository(norm)
                    persisted_repos.append(repo_record)
                    try:
                        from core.trend_tracker import trend_tracker
                        trend_tracker.record_snapshot(
                            repository_id=repo_record.id,
                            stars=repo_record.stars,
                            forks=repo_record.forks,
                            open_issues=repo_record.open_issues,
                        )
                    except Exception:
                        pass
                except Exception as exc:
                    logger.warning(f"Failed to persist repo {norm.get('full_name')}: {exc}")

        # Record search history
        RepositoryStore.log_search(
            query_string=query,
            filters={
                "mode": mode,
                "category": category,
                "language": language,
                "custom_keywords": custom_keywords,
                "page": page,
            },
            result_count=total_count,
        )

        return {
            "mode": mode,
            "query": query,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "items": normalized_repos,
            "persisted_count": len(persisted_repos),
        }

    def deep_search(
        self,
        keywords: Optional[str] = None,
        category: Optional[str] = None,
        topic: Optional[str] = None,
        language: Optional[str] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        pushed_after: Optional[str] = None,
        created_after: Optional[str] = None,
        raw_query: Optional[str] = None,
        sort: str = "stars",
        order: str = "desc",
        page: int = 1,
        per_page: int = 30,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Execute fine-grained custom deep search."""
        query = SearchEngine.build_query(
            keywords=keywords,
            category=category,
            topic=topic,
            language=language,
            min_stars=min_stars,
            max_stars=max_stars,
            pushed_after=pushed_after,
            created_after=created_after,
            raw_query=raw_query,
        )

        logger.info(f"Deep search query: '{query}' page={page}")

        raw_response = self.client.search_repositories(
            query=query,
            sort=sort,
            order=order,
            page=page,
            per_page=per_page,
        )

        raw_items = raw_response.get("items", [])
        total_count = raw_response.get("total_count", 0)

        normalized_repos = []
        for item in raw_items:
            norm = self.normalize_repository_data(item)
            normalized_repos.append(norm)
            if persist:
                try:
                    repo_record = RepositoryStore.upsert_repository(norm)
                    try:
                        from core.trend_tracker import trend_tracker
                        trend_tracker.record_snapshot(
                            repository_id=repo_record.id,
                            stars=repo_record.stars,
                            forks=repo_record.forks,
                            open_issues=repo_record.open_issues,
                        )
                    except Exception:
                        pass
                except Exception as exc:
                    logger.warning(f"Failed to persist repo {norm.get('full_name')}: {exc}")

        RepositoryStore.log_search(
            query_string=query,
            filters={
                "keywords": keywords,
                "category": category,
                "language": language,
                "min_stars": min_stars,
                "page": page,
            },
            result_count=total_count,
        )

        return {
            "query": query,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "items": normalized_repos,
        }


# Global discovery engine instance
discovery_engine = DiscoveryEngine()
