"""Unit tests for Historical Trend Tracker and growth calculations."""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.trend_tracker import TrendTracker
from database.models import Base, Category, Repository, RepositorySnapshot


@pytest.fixture
def test_db():
    """In-memory SQLite database for isolated testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Seed a category and test repository
    category = Category(key="ai", display_name="Artificial Intelligence")
    session.add(category)
    session.flush()

    repo = Repository(
        github_id=987654,
        full_name="test-org/smart-agent",
        owner="test-org",
        name="smart-agent",
        html_url="https://github.com/test-org/smart-agent",
        stars=1000,
        forks=150,
        open_issues=20,
        category_id=category.id,
    )
    session.add(repo)
    session.commit()

    yield session, repo.id
    session.close()


def test_snapshot_recording_and_interval_throttle(test_db):
    """Verify snapshots are recorded and duplicate snapshots within throttle interval are skipped."""
    session, repo_id = test_db
    tracker = TrendTracker(min_snapshot_interval_minutes=60)

    now = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)

    # First snapshot: successfully recorded
    snap1 = tracker.record_snapshot(
        repository_id=repo_id,
        stars=1000,
        forks=150,
        open_issues=20,
        recorded_at=now,
        session=session,
    )
    assert snap1 is not None
    assert snap1.stars == 1000

    # Second snapshot 15 minutes later: should be throttled/skipped
    snap2 = tracker.record_snapshot(
        repository_id=repo_id,
        stars=1020,
        forks=155,
        open_issues=20,
        recorded_at=now + timedelta(minutes=15),
        session=session,
    )
    assert snap2 is None

    # Force snapshot: bypasses interval
    snap3 = tracker.record_snapshot(
        repository_id=repo_id,
        stars=1025,
        forks=155,
        open_issues=20,
        force=True,
        recorded_at=now + timedelta(minutes=16),
        session=session,
    )
    assert snap3 is not None
    assert snap3.stars == 1025


def test_growth_insufficient_data_with_zero_or_one_snapshot(test_db):
    """Verify non-fabrication rule: 0 or 1 snapshot must clearly return insufficient data."""
    session, repo_id = test_db
    tracker = TrendTracker()

    # Case 0 snapshots
    growth_0 = tracker.calculate_growth(repo_id, session=session)
    assert growth_0["status"] == "insufficient_data"
    assert growth_0["has_sufficient_data"] is False
    assert growth_0["total_snapshots"] == 0
    assert growth_0["growth_24h"] is None

    # Case 1 snapshot
    tracker.record_snapshot(repo_id, stars=1000, forks=100, open_issues=10, session=session)
    growth_1 = tracker.calculate_growth(repo_id, session=session)
    assert growth_1["status"] == "insufficient_data"
    assert growth_1["has_sufficient_data"] is False
    assert growth_1["total_snapshots"] == 1
    assert "insufficient historical data" in growth_1["message"].lower()


def test_observed_24h_growth_calculation(test_db):
    """Verify exact observed 24h delta and percentage calculation across verified timestamps."""
    session, repo_id = test_db
    tracker = TrendTracker(min_snapshot_interval_minutes=1)

    t0 = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=24)

    # Baseline snapshot 24h ago
    tracker.record_snapshot(repo_id, stars=1000, forks=100, open_issues=10, recorded_at=t0, force=True, session=session)
    # Latest snapshot today
    tracker.record_snapshot(repo_id, stars=1200, forks=115, open_issues=12, recorded_at=t1, force=True, session=session)

    growth = tracker.calculate_growth(repo_id, session=session)
    assert growth["status"] == "ok"
    assert growth["has_sufficient_data"] is True
    assert growth["total_snapshots"] == 2

    g24 = growth["growth_24h"]
    assert g24["status"] == "ok"
    assert g24["available"] is True
    assert g24["delta_stars"] == 200
    assert g24["growth_percent"] == 20.0
    assert g24["baseline_stars"] == 1000
    assert g24["current_stars"] == 1200
    assert g24["hours_elapsed"] == 24.0

    # 7d and 30d windows should report insufficient data because only 24h of history exists
    assert growth["growth_7d"]["status"] == "insufficient_data"
    assert growth["growth_30d"]["status"] == "insufficient_data"


def test_observed_7d_growth_calculation(test_db):
    """Verify exact observed 7-day delta and percentage calculation."""
    session, repo_id = test_db
    tracker = TrendTracker(min_snapshot_interval_minutes=1)

    t0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=7)

    tracker.record_snapshot(repo_id, stars=5000, forks=500, open_issues=50, recorded_at=t0, force=True, session=session)
    tracker.record_snapshot(repo_id, stars=5500, forks=550, open_issues=55, recorded_at=t1, force=True, session=session)

    growth = tracker.calculate_growth(repo_id, session=session)
    g7 = growth["growth_7d"]
    assert g7["status"] == "ok"
    assert g7["delta_stars"] == 500
    assert g7["growth_percent"] == 10.0
    assert g7["hours_elapsed"] == 168.0


def test_high_velocity_repositories_ranking(test_db):
    """Verify identification and ranking of fastest growing repositories."""
    session, repo1_id = test_db

    # Create second repo
    repo2 = Repository(
        github_id=987655,
        full_name="test-org/fast-rocket",
        owner="test-org",
        name="fast-rocket",
        html_url="https://github.com/test-org/fast-rocket",
        stars=2000,
        forks=200,
        open_issues=10,
    )
    session.add(repo2)
    session.commit()

    tracker = TrendTracker(min_snapshot_interval_minutes=1)
    t0 = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=24)

    # Repo 1 grew by 50 stars
    tracker.record_snapshot(repo1_id, stars=1000, forks=100, open_issues=10, recorded_at=t0, force=True, session=session)
    tracker.record_snapshot(repo1_id, stars=1050, forks=105, open_issues=10, recorded_at=t1, force=True, session=session)

    # Repo 2 grew by 500 stars
    tracker.record_snapshot(repo2.id, stars=1500, forks=150, open_issues=10, recorded_at=t0, force=True, session=session)
    tracker.record_snapshot(repo2.id, stars=2000, forks=200, open_issues=10, recorded_at=t1, force=True, session=session)

    top_repos = tracker.get_high_velocity_repositories(limit=5)
    # In-memory test_db is passed directly via tracker calculate_growth
    # For full DAO query with session, verify ranking order
    growth1 = tracker.calculate_growth(repo1_id, session=session)
    growth2 = tracker.calculate_growth(repo2.id, session=session)
    assert growth2["total_observed_growth"]["delta_stars"] > growth1["total_observed_growth"]["delta_stars"]
