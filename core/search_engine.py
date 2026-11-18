"""Advanced GitHub Search Query Generator supporting 9 discovery modes and granular filters."""

from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional
from core.categorizer import categorizer

DiscoveryMode = Literal[
    "trending",
    "hidden_gems",
    "new_repositories",
    "recently_updated",
    "ai_agents",
    "trading_fintech",
    "cybersecurity",
    "devtools",
    "custom_search",
]


class SearchEngine:
    """Builds valid GitHub search query strings and manages filter constraints."""

    @staticmethod
    def build_query(
        keywords: Optional[str] = None,
        category: Optional[str] = None,
        topic: Optional[str] = None,
        language: Optional[str] = None,
        created_after: Optional[str] = None,
        pushed_after: Optional[str] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        min_forks: Optional[int] = None,
        user: Optional[str] = None,
        org: Optional[str] = None,
        is_archived: Optional[bool] = False,
        raw_query: Optional[str] = None,
    ) -> str:
        """Construct a valid GitHub search query combining all parameters."""
        parts: list[str] = []

        if raw_query and raw_query.strip():
            parts.append(raw_query.strip())

        if keywords and keywords.strip():
            parts.append(keywords.strip())

        if topic and topic.strip():
            parts.append(f"topic:{topic.strip().lower()}")

        if category and category != "all":
            cat_obj = categorizer.get_category(category)
            if cat_obj and cat_obj.subcategories:
                # Use top 3 representative topics for query containment
                top_topics = [sub.topics[0] for sub in cat_obj.subcategories[:3] if sub.topics]
                if top_topics:
                    topic_clause = " ".join([f"topic:{t}" for t in top_topics])
                    # In GitHub search, space between multiple topic filters is an implicit AND,
                    # so we pick the single most representative or broad keyword
                    parts.append(f"topic:{top_topics[0]}")

        if language and language.lower() not in ["any", "all", ""]:
            parts.append(f"language:{language.strip().lower()}")

        # Star bounds
        if min_stars is not None and max_stars is not None:
            parts.append(f"stars:{min_stars}..{max_stars}")
        elif min_stars is not None and min_stars > 0:
            parts.append(f"stars:>={min_stars}")
        elif max_stars is not None:
            parts.append(f"stars:<={max_stars}")

        # Forks
        if min_forks is not None and min_forks > 0:
            parts.append(f"forks:>={min_forks}")

        # Date qualifiers
        if created_after:
            parts.append(f"created:>={created_after}")

        if pushed_after:
            parts.append(f"pushed:>={pushed_after}")

        # User / Org
        if user and user.strip():
            parts.append(f"user:{user.strip()}")
        if org and org.strip():
            parts.append(f"org:{org.strip()}")

        # Archived filter
        if is_archived is False:
            parts.append("archived:false")
        elif is_archived is True:
            parts.append("archived:true")

        # If no keywords, topics, user, org, or stars qualifiers were provided,
        # add a default stars qualifier so GitHub API search is valid.
        has_content_filter = bool(
            raw_query or keywords or topic or (category and category != "all")
            or language or min_stars is not None or max_stars is not None
            or user or org
        )
        if not has_content_filter:
            parts.insert(0, "stars:>=50")

        return " ".join(parts)

    @classmethod
    def build_mode_query(
        cls,
        mode: DiscoveryMode,
        category: Optional[str] = None,
        language: Optional[str] = None,
        custom_keywords: Optional[str] = None,
        days_window: int = 7,
    ) -> tuple[str, str, str]:
        """
        Generate query, sort, and order parameters for the 9 discovery modes.
        Returns: (query_string, sort_field, order_direction)
        """
        now = datetime.now(timezone.utc)
        since_date = (now - timedelta(days=days_window)).strftime("%Y-%m-%d")

        if mode == "trending":
            # Repositories pushed recently with good star momentum
            kw = custom_keywords or ""
            query = cls.build_query(
                keywords=kw,
                category=category,
                language=language,
                pushed_after=since_date,
                min_stars=50,
            )
            return query, "stars", "desc"

        elif mode == "hidden_gems":
            # Modest stars (30 to 1000), low fork count, pushed recently
            kw = custom_keywords or ""
            query = cls.build_query(
                keywords=kw,
                category=category,
                language=language,
                min_stars=30,
                max_stars=1200,
                pushed_after=(now - timedelta(days=30)).strftime("%Y-%m-%d"),
            )
            return query, "updated", "desc"

        elif mode == "new_repositories":
            # Created recently (last 14 days)
            created_since = (now - timedelta(days=max(3, days_window))).strftime("%Y-%m-%d")
            query = cls.build_query(
                keywords=custom_keywords,
                category=category,
                language=language,
                created_after=created_since,
                min_stars=10,
            )
            return query, "stars", "desc"

        elif mode == "recently_updated":
            # Active commits pushed within the last 48 hours
            recent_since = (now - timedelta(days=2)).strftime("%Y-%m-%d")
            query = cls.build_query(
                keywords=custom_keywords,
                category=category,
                language=language,
                pushed_after=recent_since,
                min_stars=25,
            )
            return query, "updated", "desc"

        elif mode == "ai_agents":
            # Targeted agentic topics and keywords
            query = cls.build_query(
                topic="ai-agents",
                keywords=custom_keywords,
                category=category,
                language=language,
                min_stars=20,
            )
            return query, "stars", "desc"

        elif mode == "trading_fintech":
            # Algorithmic trading and quantitative topics
            query = cls.build_query(
                topic="algorithmic-trading",
                keywords=custom_keywords,
                category=category,
                language=language,
                min_stars=15,
            )
            return query, "stars", "desc"

        elif mode == "cybersecurity":
            # OSINT, defensive security, vulnerability research
            query = cls.build_query(
                topic="cybersecurity",
                keywords=custom_keywords,
                category=category,
                language=language,
                min_stars=20,
            )
            return query, "stars", "desc"

        elif mode == "devtools":
            # Developer productivity and CLI tools
            query = cls.build_query(
                topic="developer-tools",
                keywords=custom_keywords,
                category=category,
                language=language,
                min_stars=25,
            )
            return query, "stars", "desc"

        elif mode == "custom_search":
            query = cls.build_query(
                keywords=custom_keywords,
                category=category,
                language=language,
                min_stars=10,
            )
            return query, "stars", "desc"

        # Fallback default
        return "stars:>=50", "stars", "desc"
