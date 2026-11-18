"""Unit tests for Content Studio, prompts, draft schemas, CRUD operations, and multi-language support."""

from unittest.mock import MagicMock, patch
import pytest

from ai.analysis import ContentDraftSchema
from ai.prompts import build_content_prompt
from core.content_generator import content_generator
from database.repository_store import RepositoryStore
from services.content_service import content_service


def test_content_prompt_creation_and_languages():
    """Verify content prompt incorporates platform, language directives, and XML safety fences."""
    sample_repo = {
        "full_name": "sample/repo",
        "description": "A high-performance algorithmic bot",
        "stars": 450,
        "html_url": "https://github.com/sample/repo",
    }
    sample_dossier = {
        "verified_facts": {"primary_language": "Python"},
        "readme_claims": {
            "problem_solved": "Minimizes execution slippage in crypto trading",
            "features_claimed": "Order book matching, low latency",
            "installation_process": "pip install sample-bot",
        },
        "source_code_observations": {
            "detected_technologies": {"frameworks": ["FastAPI"]},
            "dependencies_parsed": ["fastapi", "ccxt"],
        },
    }

    # Test English YouTube prompt
    prompt_en = build_content_prompt(
        repo_data=sample_repo,
        dossier=sample_dossier,
        platform="youtube",
        content_type="script",
        language="en",
        tone="educational",
        audience_level="intermediate",
    )
    assert "PLATFORM: YOUTUBE" in prompt_en
    assert "<untrusted_repository_content>" in prompt_en
    assert "</untrusted_repository_content>" in prompt_en
    assert "fluent, natural English" in prompt_en

    # Test Bengali prompt
    prompt_bn = build_content_prompt(
        repo_data=sample_repo,
        dossier=sample_dossier,
        platform="facebook",
        content_type="post",
        language="bn",
        tone="engaging",
        audience_level="beginner",
    )
    assert "LANGUAGE: BN" in prompt_bn
    assert "Bengali (বাংলা)" in prompt_bn

    # Test Banglish prompt
    prompt_bg = build_content_prompt(
        repo_data=sample_repo,
        dossier=sample_dossier,
        platform="instagram",
        content_type="reel",
        language="banglish",
        tone="conversational",
        audience_level="intermediate",
    )
    assert "LANGUAGE: BANGLISH" in prompt_bg
    assert "Banglish" in prompt_bg


def test_content_draft_schema_and_markdown_export():
    """Verify ContentDraftSchema validation and to_markdown export formatting."""
    draft = ContentDraftSchema(
        platform="youtube",
        content_type="script",
        language="en",
        tone="educational",
        audience_level="intermediate",
        title="10x Faster Trading With SampleBot",
        hook="Stop losing money to execution slippage!",
        body="In this video we break down SampleBot...",
        practical_explanation="SampleBot uses order-book polling...",
        visual_demo_suggestions=["Terminal execution demo", "Thumbnail with high-contrast text"],
        cta="Drop a star on GitHub!",
        hashtags=["#AlgoTrading", "#Python", "#OpenSource"],
        source_url="https://github.com/sample/repo",
    )

    md = draft.to_markdown()
    assert "# 10x Faster Trading With SampleBot" in md
    assert "## 🪝 Opening Hook" in md
    assert "## 📝 Main Content" in md
    assert "## 🎬 Suggested Visuals / Demo Concepts" in md
    assert "Terminal execution demo" in md
    assert "https://github.com/sample/repo" in md
    assert "#AlgoTrading" in md


def test_deterministic_generator_languages():
    """Verify deterministic generator produces complete drafts across EN, BN, and Banglish without AI."""
    sample_repo = {
        "full_name": "test/quant-bot",
        "description": "Automated quant bot",
        "stars": 320,
        "html_url": "https://github.com/test/quant-bot",
    }
    sample_dossier = {
        "verified_facts": {"primary_language": "Python"},
        "readme_claims": {
            "problem_solved": "Automates grid trading strategies",
            "features_claimed": "Backtesting engine, paper trading",
            "installation_process": "pip install quant-bot",
        },
        "source_code_observations": {
            "detected_technologies": {},
            "dependencies_parsed": ["pandas"],
        },
    }

    # 1. English
    draft_en = content_generator.generate_deterministic_draft(
        repo_data=sample_repo,
        dossier=sample_dossier,
        platform="youtube",
        content_type="script",
        language="en",
        tone="educational",
        audience_level="intermediate",
    )
    assert "test/quant-bot" in draft_en.title
    assert len(draft_en.hook) > 10
    assert len(draft_en.body) > 50

    # 2. Bengali
    draft_bn = content_generator.generate_deterministic_draft(
        repo_data=sample_repo,
        dossier=sample_dossier,
        platform="facebook",
        content_type="post",
        language="bn",
        tone="educational",
        audience_level="beginner",
    )
    assert "ওপেন সোর্স" in draft_bn.title
    assert "বাংলাটেক" in " ".join(draft_bn.hashtags)

    # 3. Banglish
    draft_bg = content_generator.generate_deterministic_draft(
        repo_data=sample_repo,
        dossier=sample_dossier,
        platform="shorts",
        content_type="script",
        language="banglish",
        tone="conversational",
        audience_level="intermediate",
    )
    assert "Review" in draft_bg.title
    assert "GitHub" in draft_bg.hook


def test_content_service_draft_crud():
    """Verify ContentService creates, retrieves, updates, lists, and deletes drafts in SQLite."""
    # Ensure a repository exists
    repo = RepositoryStore.upsert_repository({
        "github_id": 999888,
        "full_name": "crud-test/content-repo",
        "owner": "crud-test",
        "name": "content-repo",
        "html_url": "https://github.com/crud-test/content-repo",
        "stars": 150,
    })

    schema = ContentDraftSchema(
        platform="youtube",
        content_type="script",
        language="en",
        tone="educational",
        audience_level="intermediate",
        title="Initial Draft Title",
        hook="Initial Hook",
        body="Initial Body Text",
        practical_explanation="How to use it",
        visual_demo_suggestions=["Demo 1"],
        cta="Star on GitHub",
        hashtags=["#Test"],
        source_url="https://github.com/crud-test/content-repo",
    )

    # 1. Create Draft
    saved_draft = content_service.save_draft(repository_id=repo.id, schema=schema)
    assert saved_draft.id is not None
    assert saved_draft.title == "Initial Draft Title"
    draft_id = saved_draft.id

    # 2. Get Draft
    fetched = content_service.get_draft(draft_id)
    assert fetched is not None
    assert fetched["title"] == "Initial Draft Title"
    assert fetched["repository_name"] == "crud-test/content-repo"

    # 3. Update Draft
    schema.title = "Updated Draft Title"
    schema.body = "Updated Body Text"
    updated_draft = content_service.save_draft(repository_id=repo.id, schema=schema, draft_id=draft_id)
    assert updated_draft.id == draft_id
    assert updated_draft.title == "Updated Draft Title"

    # 4. List Drafts
    drafts_list = content_service.list_drafts(repository_id=repo.id)
    assert len(drafts_list) >= 1
    assert any(d["id"] == draft_id for d in drafts_list)

    # 5. Delete Draft
    deleted = content_service.delete_draft(draft_id)
    assert deleted is True
    assert content_service.get_draft(draft_id) is None


def test_missing_ai_provider_fallback_to_deterministic():
    """Verify ContentGenerator seamlessly uses deterministic fallback when AI provider is None."""
    with patch("core.content_generator.get_ai_provider", return_value=None):
        schema, mode = content_generator.generate(
            repo_data={"full_name": "ai-none/test", "stars": 50, "html_url": "https://github.com/ai-none/test"},
            dossier={"verified_facts": {}, "readme_claims": {}, "source_code_observations": {}},
            platform="youtube",
            content_type="script",
            language="en",
            tone="educational",
            audience_level="intermediate",
        )
        assert mode == "deterministic"
        assert isinstance(schema, ContentDraftSchema)
        assert "ai-none/test" in schema.title
