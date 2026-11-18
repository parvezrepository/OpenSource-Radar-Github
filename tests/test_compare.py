"""Unit tests for the multi-repository comparison matrix engine."""

from unittest.mock import MagicMock, patch
import pytest

from core.comparison_engine import ComparisonEngine
from core.repository_analyzer import RepositoryAnalyzer


def test_comparison_invalid_count():
    """Verify ValueError is raised if < 2 or > 5 repositories are supplied."""
    engine = ComparisonEngine()

    with pytest.raises(ValueError) as exc1:
        engine.compare_repositories(["only/one"])
    assert "at least 2" in str(exc1.value).lower()

    with pytest.raises(ValueError) as exc2:
        engine.compare_repositories(["r1/a", "r2/b", "r3/c", "r4/d", "r5/e", "r6/f"])
    assert "maximum 5" in str(exc2.value).lower()


@patch.object(RepositoryAnalyzer, "analyze_repository")
def test_comparison_matrix_structure(mock_analyze):
    """Verify comparison matrix aggregates metrics and dependencies accurately."""
    mock_dossier_a = {
        "repository": {
            "full_name": "org/repo-a",
            "stars": 1000,
            "forks": 150,
            "open_issues": 10,
            "license": "MIT",
            "default_branch": "main",
        },
        "verified_facts": {
            "primary_language": "Python",
            "has_test_suite": True,
            "has_dockerfile": True,
            "last_commit_date": "2026-03-01",
        },
        "readme_claims": {
            "features_claimed": "Feature A1, Feature A2",
            "problem_solved": "Problem A",
            "limitations_reported": "None reported",
        },
        "source_code_observations": {
            "detected_technologies": {"frameworks": ["FastAPI"]},
            "dependencies_parsed": ["fastapi", "pydantic", "requests"],
        },
        "raw_readme": "# Repo A",
    }

    mock_dossier_b = {
        "repository": {
            "full_name": "org/repo-b",
            "stars": 500,
            "forks": 75,
            "open_issues": 5,
            "license": "Apache-2.0",
            "default_branch": "main",
        },
        "verified_facts": {
            "primary_language": "Python",
            "has_test_suite": True,
            "has_dockerfile": False,
            "last_commit_date": "2026-03-02",
        },
        "readme_claims": {
            "features_claimed": "Feature B1",
            "problem_solved": "Problem B",
            "limitations_reported": "None reported",
        },
        "source_code_observations": {
            "detected_technologies": {"frameworks": ["Flask"]},
            "dependencies_parsed": ["flask", "pydantic", "requests"],
        },
        "raw_readme": "# Repo B",
    }

    mock_analyze.side_effect = [mock_dossier_a, mock_dossier_b]

    engine = ComparisonEngine()
    matrix = engine.compare_repositories(["org/repo-a", "org/repo-b"])

    assert len(matrix["repositories"]) == 2
    assert "org/repo-a" in matrix["metrics"]["stars"]
    assert matrix["metrics"]["stars"]["org/repo-a"] == 1000
    assert matrix["metrics"]["stars"]["org/repo-b"] == 500

    # Common dependency intersection
    assert "pydantic" in matrix["common_dependencies"]
    assert "requests" in matrix["common_dependencies"]
    assert "fastapi" not in matrix["common_dependencies"]  # Only in A
