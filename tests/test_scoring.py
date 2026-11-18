"""Unit tests for the explainable 0–100 Content Opportunity Scoring Engine."""

from datetime import datetime, timezone
import pytest
from core.scoring_engine import scoring_engine


def test_scoring_calculation_5_pillars():
    """Verify points calculation across all 5 pillars and bounds within 0-100."""
    sample_dossier = {
        "repository": {
            "stars": 850,
            "forks": 120,
            "open_issues": 15,
            "license": "Apache-2.0",
            "is_archived": False,
            "pushed_at": datetime.now(timezone.utc).isoformat(),
            "description": "An autonomous multi-agent framework for quantitative backtesting.",
        },
        "verified_facts": {
            "primary_language": "Python",
            "has_test_suite": True,
            "has_ci_pipeline": True,
            "has_dockerfile": True,
            "last_commit_date": datetime.now(timezone.utc).isoformat(),
        },
        "readme_claims": {
            "overview": "Comprehensive autonomous agent package.",
            "problem_solved": "Solves real-time portfolio management latency for automated high-frequency hedge fund trading strategies.",
            "features_claimed": "Distributed memory, fast backtesting engine, automated execution.",
            "installation_process": "pip install agent-quant",
            "usage_instructions": "import agent_quant; agent_quant.run()",
            "limitations_reported": "Requires Python 3.11+",
        },
        "source_code_observations": {
            "detected_technologies": {
                "frameworks": ["PyTorch", "LangChain"],
                "databases": ["Redis"],
            },
            "dependencies_parsed": ["torch", "langchain", "redis", "pydantic"],
        },
        "raw_readme": "# Agent Quant\n![Demo](https://example.com/demo.gif)\n```bash\npip install agent-quant\n```",
    }

    report = scoring_engine.calculate_score(sample_dossier, has_historical_snapshots=False)

    assert 0 <= report.total_score <= 100
    assert report.total_score >= 70  # Strong project should score high
    assert report.is_preliminary is True  # Snapshot pending

    # Validate individual pillars
    assert 0 <= report.trend_momentum.score <= 25
    assert 0 <= report.uniqueness.score <= 20
    assert 0 <= report.practical_usefulness.score <= 20
    assert 0 <= report.content_appeal.score <= 20
    assert 0 <= report.quality_signals.score <= 15


def test_score_explanations_and_reasons():
    """Verify explainable score output provides positive reasons and identifies missing signals."""
    sparse_dossier = {
        "repository": {
            "stars": 5,
            "forks": 0,
            "open_issues": 0,
            "license": "None",
            "is_archived": False,
            "pushed_at": "2020-01-01T00:00:00Z",
            "description": "",
        },
        "verified_facts": {
            "primary_language": "Python",
            "has_test_suite": False,
            "has_ci_pipeline": False,
            "has_dockerfile": False,
        },
        "readme_claims": {
            "problem_solved": "Not specified in repository README.",
            "installation_process": "Not specified in repository README.",
            "usage_instructions": "Not specified in repository README.",
        },
        "source_code_observations": {
            "detected_technologies": {},
            "dependencies_parsed": [],
        },
        "raw_readme": "",
    }

    report = scoring_engine.calculate_score(sparse_dossier)
    assert report.total_score < 40
    # Must have explanatory reasons and missing signal flags
    assert len(report.to_dict()["missing_signals"]) > 0
    assert any("license" in m.lower() for m in report.to_dict()["missing_signals"])
