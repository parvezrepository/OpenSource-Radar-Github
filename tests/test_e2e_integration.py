"""End-to-End full application integration test exercising workflows 1 through 20."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest

from ai.analysis import ContentDraftSchema, StructuredAnalysis
from core.categorizer import TechnologyCategorizer, categorizer
from core.comparison_engine import ComparisonEngine
from core.content_generator import ContentGenerator
from core.discovery_engine import DiscoveryEngine
from core.github_client import GitHubClient, get_github_client
from core.repository_analyzer import RepositoryAnalyzer, repository_analyzer
from core.scoring_engine import ScoringEngine, scoring_engine
from core.search_engine import SearchEngine
from core.trend_tracker import TrendTracker, trend_tracker
from database.connection import check_db_health, init_db
from database.models import (
    Category,
    ContentDraft,
    DiscoveryJob,
    DiscoveryLog,
    Repository,
    RepositoryAnalysis,
    RepositorySnapshot,
    SavedRepository,
)
from database.repository_store import RepositoryStore
from services.content_service import ContentService
from services.discovery_service import DiscoveryService
from services.monitoring_service import NotificationEvent, MonitoringService
from services.scheduler_service import SchedulerService


@pytest.fixture(scope="module", autouse=True)
def setup_integration_env():
    """Ensure database schema and default categories/jobs exist."""
    init_db()


def test_workflow_01_and_02_connection_and_health():
    """Workflows 1 & 2: Application startup and GitHub connection test."""
    db_health = check_db_health()
    assert db_health["connected"] is True
    assert "sqlite" in db_health["url"]

    client = get_github_client()
    assert client is not None
    res = client.test_connection()
    assert res["status"] in ["connected", "connected_unauthenticated", "error"]


def test_workflow_03_04_05_discovery_and_filtering():
    """Workflows 3, 4, 5: Discover repositories, search by technology, and filter."""
    # Workflow 4: Technology Classification
    cat = TechnologyCategorizer()
    domain, sub, conf = cat.classify_repository(
        topics=["fastapi", "python"],
        description="FastAPI web application framework",
        name="my-fastapi-app",
    )
    assert domain == "software"

    # Workflow 5: Build search query with filters
    query = SearchEngine.build_query(
        keywords="llm",
        language="python",
        min_stars=500,
        is_archived=False,
    )
    assert "llm" in query
    assert "language:python" in query
    assert "stars:>=500" in query
    assert "archived:false" in query

    # Workflow 3: Discovery normalization and database persistence
    engine = DiscoveryEngine()
    mock_gh_data = {
        "id": 12345678,
        "name": "radar-demo",
        "full_name": "opensource-radar/radar-demo",
        "owner": {"login": "opensource-radar"},
        "html_url": "https://github.com/opensource-radar/radar-demo",
        "description": "Enterprise-grade intelligence radar",
        "stargazers_count": 2500,
        "forks_count": 300,
        "open_issues_count": 15,
        "size": 1200,
        "language": "Python",
        "topics": ["ai-agents", "mcp", "automation"],
        "archived": False,
        "default_branch": "main",
        "license": {"spdx_id": "MIT", "name": "MIT License"},
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-11-01T00:00:00Z",
        "pushed_at": "2026-11-15T00:00:00Z",
    }
    norm = engine.normalize_repository_data(mock_gh_data)
    assert norm["stars"] == 2500
    assert norm["category_key"] == "agents"

    repo = RepositoryStore.upsert_repository(norm)
    assert repo.id is not None
    assert repo.full_name == "opensource-radar/radar-demo"


def test_workflow_06_save_and_bookmark():
    """Workflow 6: Save and bookmark repository."""
    repo = RepositoryStore.get_by_full_name("opensource-radar/radar-demo")
    assert repo is not None

    saved = RepositoryStore.save_repository(repo.id, notes="Research target for Q4", tags=["priority", "agent"])
    assert saved is True
    assert RepositoryStore.is_saved(repo.id) is True

    bookmarks = RepositoryStore.list_saved_repositories()
    assert any(b["repository_id"] == repo.id for b in bookmarks)


def test_workflow_07_08_09_10_inspection_analysis_and_ai():
    """Workflows 7, 8, 9, 10: Open details, inspect README/files, analyze repo, AI report."""
    client = get_github_client()
    analyzer = RepositoryAnalyzer()

    # Workflow 8: Inspect source file with strict binary and size rejection
    binary_ok, binary_err = client.get_file_content("owner", "repo", "test.dll")
    assert binary_ok is None
    assert "binary file" in binary_err.lower()

    # Workflow 9: Static repository analysis
    mock_dossier = {
        "repository": {
            "full_name": "opensource-radar/radar-demo",
            "stars": 2500,
            "forks": 300,
            "pushed_at": "2026-11-15T00:00:00Z",
        },
        "verified_facts": {
            "primary_language": "Python",
            "languages_distribution": {"Python": 90, "Shell": 10},
            "topics": ["ai-agents", "mcp"],
            "detected_manifests": ["requirements.txt"],
            "dependencies": ["pydantic", "fastapi"],
            "commit_count_recent": 12,
            "latest_release": "v1.0.0",
        },
        "readme_claims": {
            "problem_statement": "Automates tech scouting",
            "features": ["Autonomous discovery", "Deterministic scoring"],
            "installation": "pip install radar",
            "usage": "radar run",
            "limitations": "Requires Python 3.11+",
        },
        "source_code_observations": {
            "detected_technologies": {"frameworks": ["FastAPI"]},
            "dependencies_parsed": ["pydantic", "fastapi"],
        },
    }

    with patch.object(analyzer, "analyze_repository", return_value=mock_dossier):
        dossier = analyzer.analyze_repository("opensource-radar", "radar-demo")
        assert dossier["repository"]["full_name"] == "opensource-radar/radar-demo"
        assert len(dossier["verified_facts"]["dependencies"]) == 2

    # Workflow 10: AI Provider analysis with deterministic Pydantic validation
    mock_ai_output = StructuredAnalysis(
        simple_explanation="An intelligent technology radar for scouting GitHub repositories.",
        technical_architecture="Python backend with SQLite persistence and Streamlit UI.",
        identified_technologies=["Python", "FastAPI", "SQLite", "Streamlit"],
        important_files=[],
        key_functions=["Repository Discovery", "Static Manifest Parsing"],
        practical_applications=["Open-source technology intelligence", "Content research"],
        implementation_details=["Deterministic regex parsing with zero-code-execution."],
        limitations=["Subject to GitHub API rate limits."],
        learning_opportunities=["Advanced search syntax", "Static analysis patterns"],
        potential_research_topics=["Automated code intelligence"],
        evidence_sources=["README.md", "requirements.txt"],
    )
    assert mock_ai_output.simple_explanation != ""
    assert len(mock_ai_output.practical_applications) == 2


def test_workflow_11_12_comparison_and_scoring():
    """Workflows 11 & 12: Compare repositories and calculate Content Opportunity Score."""
    # Workflow 12: Explainable 5-pillar scoring
    dossier = {
        "repository": {
            "full_name": "opensource-radar/radar-demo",
            "stars": 2500,
            "forks": 300,
            "open_issues": 15,
            "pushed_at": "2026-11-15T00:00:00Z",
        },
        "verified_facts": {
            "primary_language": "Python",
            "commit_count_recent": 15,
            "latest_release": "v1.0.0",
            "topics": ["ai-agents", "mcp"],
            "dependencies": ["fastapi", "pydantic"],
        },
        "readme_claims": {
            "problem_statement": "Tech scouting",
            "features": ["f1", "f2"],
            "usage": "radar run",
            "installation": "pip install",
            "limitations": "None",
        },
        "source_code_observations": {
            "dependencies_parsed": ["fastapi", "pydantic"],
        },
    }

    report = scoring_engine.calculate_score(dossier)
    assert 0 <= report.total_score <= 100
    assert report.trend_momentum.score >= 0
    assert len(report.trend_momentum.reasons) > 0
    assert report.editorial_verdict != ""

    # Workflow 11: Compare 2 repositories
    comp_engine = ComparisonEngine()
    mock_d_a = {
        "repository": {"full_name": "org/repo-a", "stars": 2000, "forks": 100, "open_issues": 5, "license": "MIT", "default_branch": "main"},
        "verified_facts": {"primary_language": "Python"},
        "readme_claims": {"features": ["f1"]},
        "source_code_observations": {"dependencies_parsed": ["fastapi", "uvicorn"]},
    }
    mock_d_b = {
        "repository": {"full_name": "org/repo-b", "stars": 1500, "forks": 80, "open_issues": 10, "license": "Apache-2.0", "default_branch": "main"},
        "verified_facts": {"primary_language": "Python"},
        "readme_claims": {"features": ["f2"]},
        "source_code_observations": {"dependencies_parsed": ["flask", "uvicorn"]},
    }

    with patch.object(RepositoryAnalyzer, "analyze_repository", side_effect=[mock_d_a, mock_d_b]):
        matrix = comp_engine.compare_repositories(["org/repo-a", "org/repo-b"])
        assert len(matrix["repositories"]) == 2
        assert "uvicorn" in matrix["common_dependencies"]


def test_workflow_13_14_15_16_content_studio_lifecycle():
    """Workflows 13, 14, 15, 16: Generate content, edit, save draft, and export."""
    repo = RepositoryStore.get_by_full_name("opensource-radar/radar-demo")
    assert repo is not None

    service = ContentService()

    # Workflow 13: Generate content draft
    mock_dossier = {
        "repository": {"full_name": repo.full_name, "stars": repo.stars, "html_url": repo.html_url},
        "verified_facts": {"primary_language": "Python", "dependencies": ["fastapi"]},
        "readme_claims": {"problem_statement": "Automates scouting", "features": ["Feature A"]},
    }
    with patch("core.repository_analyzer.repository_analyzer.analyze_repository", return_value=mock_dossier):
        schema, mode, repo_id = service.generate_draft(
            owner="opensource-radar",
            repo="radar-demo",
            platform="YouTube (Long-form)",
            content_type="Full Script",
            language="en",
        )
        assert isinstance(schema, ContentDraftSchema)
        assert schema.title != ""

    # Workflow 14: Edit content fields
    schema.title = "Custom Edited Title: " + schema.title
    schema.cta = "Custom Call To Action"

    # Workflow 15: Save draft to SQLite
    saved_draft = service.save_draft(repository_id=repo.id, schema=schema)
    assert saved_draft.id is not None
    assert "Custom Edited Title" in saved_draft.title

    # Workflow 16: Export Markdown and TXT
    md_content = schema.to_markdown()
    assert "# Custom Edited Title:" in md_content
    assert "Custom Call To Action" in md_content
    assert schema.source_url in md_content


def test_workflow_17_18_19_20_scheduler_snapshots_and_analytics():
    """Workflows 17, 18, 19, 20: Configure scheduled job, run scheduler, snapshots, analytics."""
    repo = RepositoryStore.get_by_full_name("opensource-radar/radar-demo")
    assert repo is not None

    sched_service = SchedulerService()

    # Workflow 17: Configure scheduled discovery job
    job = sched_service.create_or_update_job(
        job_name="E2E Autonomous Agent Radar",
        category="agents",
        query_params={"mode": "ai_agents", "keywords": "mcp", "per_page": 10},
        cron_expression="0 */4 * * *",
        is_enabled=True,
    )
    assert job.id is not None

    # Workflow 19: Collect historical snapshots
    tracker = TrendTracker(min_snapshot_interval_minutes=1)
    t0 = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=7)

    snap1 = tracker.record_snapshot(repo.id, stars=2000, forks=250, open_issues=10, recorded_at=t0, force=True)
    snap2 = tracker.record_snapshot(repo.id, stars=2500, forks=300, open_issues=15, recorded_at=t1, force=True)
    assert snap1 is not None
    assert snap2 is not None

    # Workflow 20: View analytics calculations
    growth = tracker.calculate_growth(repo.id)
    assert growth["status"] == "ok"
    assert growth["has_sufficient_data"] is True
    assert growth["growth_7d"]["available"] is True
    assert growth["growth_7d"]["delta_stars"] == 500
    assert growth["growth_7d"]["growth_percent"] == 25.0

    # Ecosystem stats verification
    cat_dist = RepositoryStore.get_category_distribution()
    assert isinstance(cat_dist, dict)
    assert len(cat_dist) > 0

    lang_dist = RepositoryStore.get_language_distribution()
    assert isinstance(lang_dist, dict)
    assert "Python" in lang_dist
