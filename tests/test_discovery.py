"""Unit tests for DiscoveryEngine, Categorizer, and persistence."""

from unittest.mock import MagicMock
import pytest

from core.categorizer import categorizer
from core.discovery_engine import DiscoveryEngine
from core.github_client import GitHubClient, GitHubRateLimitError, GitHubValidationError
from database.models import Repository
from database.repository_store import RepositoryStore


def test_categorizer_classification():
    """Verify topic-based and keyword-based repository classification."""
    # Test AI / Agent topics
    cat1, sub1, conf1 = categorizer.classify_repository(
        topics=["mcp", "autonomous-agents"],
        description="A framework for autonomous multi-agent systems",
        name="agent-swarm",
    )
    assert cat1 == "agents"
    assert conf1 >= 0.5

    # Test FinTech / Trading
    cat2, sub2, conf2 = categorizer.classify_repository(
        topics=["backtesting", "algorithmic-trading"],
        description="Python quantitative trading strategy backtester",
        name="quant-engine",
    )
    assert cat2 == "fintech"
    assert conf2 >= 0.5

    # Test Security
    cat3, sub3, conf3 = categorizer.classify_repository(
        topics=["osint", "reconnaissance"],
        description="Open source intelligence tools",
        name="recon-cli",
    )
    assert cat3 == "security"


def test_repository_normalization_and_16_fields():
    """Verify that all 16 required repository fields are extracted and normalized."""
    mock_item = {
        "id": 888123,
        "full_name": "test-org/ai-tool",
        "name": "ai-tool",
        "owner": {"login": "test-org"},
        "html_url": "https://github.com/test-org/ai-tool",
        "description": "An AI deep learning package",
        "stargazers_count": 1250,
        "forks_count": 140,
        "open_issues_count": 12,
        "size": 4096,
        "language": "Python",
        "topics": ["pytorch", "deep-learning"],
        "license": {"spdx_id": "MIT", "name": "MIT License"},
        "default_branch": "main",
        "archived": False,
        "created_at": "2026-01-10T14:30:00Z",
        "updated_at": "2026-03-01T10:00:00Z",
        "pushed_at": "2026-03-05T08:15:00Z",
    }

    engine = DiscoveryEngine()
    norm = engine.normalize_repository_data(mock_item)

    # Validate all 16 fields
    assert norm["github_id"] == 888123
    assert norm["full_name"] == "test-org/ai-tool"
    assert norm["owner"] == "test-org"
    assert norm["name"] == "ai-tool"
    assert norm["html_url"] == "https://github.com/test-org/ai-tool"
    assert norm["description"] == "An AI deep learning package"
    assert norm["stars"] == 1250
    assert norm["forks"] == 140
    assert norm["open_issues"] == 12
    assert norm["repo_size_kb"] == 4096
    assert norm["primary_language"] == "Python"
    assert norm["topics"] == ["pytorch", "deep-learning"]
    assert norm["license_key"] == "MIT"
    assert norm["default_branch"] == "main"
    assert norm["is_archived"] is False
    assert norm["pushed_at_github"] is not None


def test_discovery_pagination_and_duplicate_prevention():
    """Verify discovery engine handles pagination and updates existing records without duplicating."""
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.search_repositories.return_value = {
        "total_count": 1,
        "items": [
            {
                "id": 777001,
                "full_name": "duplicate-test/repo",
                "name": "repo",
                "owner": {"login": "duplicate-test"},
                "html_url": "https://github.com/duplicate-test/repo",
                "description": "First discovery run",
                "stargazers_count": 100,
                "forks_count": 10,
                "open_issues_count": 1,
                "language": "Python",
                "topics": ["cli"],
            }
        ],
    }

    engine = DiscoveryEngine(github_client=mock_client)

    # First discovery
    res1 = engine.discover(mode="devtools", page=1, per_page=10, persist=True)
    assert res1["total_count"] == 1
    assert len(res1["items"]) == 1

    fetched1 = RepositoryStore.get_by_github_id(777001)
    assert fetched1 is not None
    assert fetched1.stars == 100

    # Second discovery with updated stars (simulating subsequent crawl)
    mock_client.search_repositories.return_value["items"][0]["stargazers_count"] = 150
    mock_client.search_repositories.return_value["items"][0]["description"] = "Second discovery run"

    res2 = engine.discover(mode="devtools", page=1, per_page=10, persist=True)
    fetched2 = RepositoryStore.get_by_github_id(777001)

    assert fetched2.id == fetched1.id  # Same primary key, no duplicate row
    assert fetched2.stars == 150
    assert fetched2.description == "Second discovery run"


def test_discovery_empty_results():
    """Verify discovery engine returns clean empty structure on zero matches."""
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.search_repositories.return_value = {
        "total_count": 0,
        "items": [],
    }

    engine = DiscoveryEngine(github_client=mock_client)
    res = engine.discover(mode="hidden_gems", custom_keywords="nonexistentxyz123", persist=True)
    assert res["total_count"] == 0
    assert res["items"] == []


def test_discovery_rate_limit_handling():
    """Verify discovery engine propagates GitHubRateLimitError cleanly."""
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.search_repositories.side_effect = GitHubRateLimitError("Rate limit reached", status_code=403)

    engine = DiscoveryEngine(github_client=mock_client)
    with pytest.raises(GitHubRateLimitError):
        engine.discover(mode="trending")


def test_discovery_invalid_query_handling():
    """Verify discovery engine handles invalid query errors gracefully."""
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.search_repositories.side_effect = GitHubValidationError("Invalid syntax", status_code=422)

    engine = DiscoveryEngine(github_client=mock_client)
    with pytest.raises(GitHubValidationError):
        engine.deep_search(raw_query="invalid::query::syntax")
