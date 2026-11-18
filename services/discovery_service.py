"""Service layer coordinating discovery workflows between UI, core engines, and storage."""

import logging
from typing import Any, Optional
from core.discovery_engine import discovery_engine
from core.search_engine import DiscoveryMode
from database.repository_store import RepositoryStore

logger = logging.getLogger("opensource_radar.service.discovery")


class DiscoveryService:
    """Provides high-level discovery operations with persistence and error wrapping."""

    @staticmethod
    def run_discovery(
        mode: DiscoveryMode = "trending",
        category: Optional[str] = None,
        language: Optional[str] = None,
        keywords: Optional[str] = None,
        days_window: int = 7,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """Execute discovery and return normalized repository results."""
        return discovery_engine.discover(
            mode=mode,
            category=category,
            language=language,
            custom_keywords=keywords,
            days_window=days_window,
            page=page,
            per_page=per_page,
            persist=True,
        )

    @staticmethod
    def run_custom_search(
        keywords: Optional[str] = None,
        category: Optional[str] = None,
        topic: Optional[str] = None,
        language: Optional[str] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        sort: str = "stars",
        order: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """Execute custom deep search with multi-parameter filtering."""
        return discovery_engine.deep_search(
            keywords=keywords,
            category=category,
            topic=topic,
            language=language,
            min_stars=min_stars,
            max_stars=max_stars,
            sort=sort,
            order=order,
            page=page,
            per_page=per_page,
            persist=True,
        )


discovery_service = DiscoveryService()
