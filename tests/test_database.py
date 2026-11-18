"""Unit tests for database initialization, models, and repository store."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import select

from database.connection import check_db_health, get_db, init_db
from database.migrations import run_migrations
from database.models import (
    AppSettings,
    Category,
    ContentDraft,
    DiscoveryJob,
    DiscoveryLog,
    Repository,
    RepositoryAnalysis,
    RepositorySnapshot,
    SavedRepository,
    SearchHistory,
)
from database.repository_store import RepositoryStore


def test_database_initialization_and_health():
    """Verify database initializes properly and health check passes."""
    run_migrations()
    health = check_db_health()
    assert health["connected"] is True
    assert health["status"] == "healthy"


def test_seeded_categories():
    """Verify all 8 predefined technology categories exist."""
    with get_db() as session:
        cats = session.execute(select(Category)).scalars().all()
        keys = {c.key for c in cats}
        assert "ai" in keys
        assert "agents" in keys
        assert "fintech" in keys
        assert "security" in keys
        assert len(cats) >= 8


def test_repository_upsert_and_deduplication():
    """Verify repository insertion and duplicate prevention by github_id."""
    sample_repo = {
        "github_id": 999001,
        "full_name": "test-owner/test-repo",
        "owner": "test-owner",
        "name": "test-repo",
        "html_url": "https://github.com/test-owner/test-repo",
        "description": "Initial test description",
        "stars": 150,
        "forks": 25,
        "open_issues": 3,
        "primary_language": "Python",
        "topics": ["ai", "testing"],
    }

    # First insert
    repo1 = RepositoryStore.upsert_repository(sample_repo)
    assert repo1.id is not None
    assert repo1.stars == 150

    # Retrieve by github_id
    fetched = RepositoryStore.get_by_github_id(999001)
    assert fetched is not None
    assert fetched.full_name == "test-owner/test-repo"

    # Update volatile metrics (same github_id)
    updated_data = sample_repo.copy()
    updated_data["stars"] = 200
    updated_data["description"] = "Updated description"
    repo2 = RepositoryStore.upsert_repository(updated_data)

    assert repo2.id == repo1.id  # Same database record
    assert repo2.stars == 200
    assert repo2.description == "Updated description"


def test_bookmark_and_saved_repositories():
    """Verify saving, listing, and unsaving a repository."""
    # Ensure a repository exists
    repo = RepositoryStore.upsert_repository({
        "github_id": 999002,
        "full_name": "bookmark-test/repo",
        "owner": "bookmark-test",
        "name": "repo",
        "html_url": "https://github.com/bookmark-test/repo",
        "stars": 500,
    })

    # Bookmark
    saved = RepositoryStore.save_repository(repo.id, notes="Important paper implementation", tags=["research", "ai"])
    assert saved is True
    assert RepositoryStore.is_saved(repo.id) is True

    # List saved
    saved_list = RepositoryStore.list_saved_repositories()
    saved_ids = [item["repository_id"] for item in saved_list]
    assert repo.id in saved_ids

    # Unsave
    unsaved = RepositoryStore.unsave_repository(repo.id)
    assert unsaved is True
    assert RepositoryStore.is_saved(repo.id) is False


def test_overview_stats():
    """Verify overview stats return expected keys and counts."""
    stats = RepositoryStore.get_overview_stats()
    assert "total_discovered" in stats
    assert "total_saved" in stats
    assert "total_analyzed" in stats
    assert "total_drafts" in stats
    assert "recent_repositories" in stats
    assert stats["total_discovered"] >= 1
