"""Unit tests for SearchEngine and query generation syntax."""

import pytest
from core.search_engine import SearchEngine


def test_basic_query_generation():
    """Verify standard keyword and language query syntax."""
    q = SearchEngine.build_query(keywords="fastapi", language="python", min_stars=100)
    assert "fastapi" in q
    assert "language:python" in q
    assert "stars:>=100" in q
    assert "archived:false" in q


def test_star_range_query():
    """Verify star range boundary formatting."""
    q = SearchEngine.build_query(keywords="agent", min_stars=50, max_stars=500)
    assert "stars:50..500" in q


def test_date_and_user_qualifiers():
    """Verify pushed_after, created_after, user, and org filters."""
    q = SearchEngine.build_query(
        user="testuser",
        pushed_after="2026-01-01",
        created_after="2025-01-01",
        is_archived=True,
    )
    assert "user:testuser" in q
    assert "pushed:>=2026-01-01" in q
    assert "created:>=2025-01-01" in q
    assert "archived:true" in q


def test_all_discovery_modes():
    """Verify all 9 discovery modes generate valid query, sort, and order tuples."""
    modes = [
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
    for mode in modes:
        query, sort, order = SearchEngine.build_mode_query(mode=mode, language="python")
        assert len(query) > 0, f"Mode '{mode}' generated empty query."
        assert sort in ["stars", "forks", "updated"]
        assert order in ["asc", "desc"]


def test_empty_query_default():
    """Verify empty query inputs fallback to safe stars default."""
    q = SearchEngine.build_query()
    assert "stars:>=50" in q
