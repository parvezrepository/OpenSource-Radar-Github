"""Tests for Chat with Repository (AI Q&A Assistant) functionality."""

from unittest.mock import MagicMock, patch
import pytest

from ai.prompts import build_chat_prompt
from core.repository_analyzer import RepositoryAnalyzer


@pytest.fixture
def sample_dossier():
    """Return a representative static repository dossier for tests."""
    return {
        "repository": {
            "github_id": 12345,
            "full_name": "tiangolo/fastapi",
            "owner": "tiangolo",
            "name": "fastapi",
            "html_url": "https://github.com/tiangolo/fastapi",
            "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production.",
            "stars": 75000,
            "forks": 6200,
            "license": "MIT License",
        },
        "verified_facts": {
            "primary_language": "Python",
            "has_test_suite": True,
            "has_dockerfile": True,
            "has_ci_pipeline": True,
            "latest_release_tag": "0.111.0",
        },
        "source_code_observations": {
            "detected_technologies": {"frameworks": ["Starlette", "Pydantic"], "databases": []},
            "dependencies_parsed": ["starlette", "pydantic", "typing-extensions"],
        },
        "file_tree": ["fastapi/__init__.py", "fastapi/applications.py", "Dockerfile", "pyproject.toml"],
        "raw_readme": "# FastAPI\n\nFastAPI is a modern, fast web framework for building APIs with Python.",
    }


def test_build_chat_prompt_structure(sample_dossier):
    """Verify build_chat_prompt includes XML safety fences, facts, and user query."""
    query = "Does this project have Docker support?"
    chat_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help you with this repository?"},
    ]

    prompt = build_chat_prompt(dossier=sample_dossier, query=query, chat_history=chat_history)
    assert "<untrusted_repository_content>" in prompt
    assert "</untrusted_repository_content>" in prompt
    assert "tiangolo/fastapi" in prompt
    assert "Starlette" in prompt
    assert "Does this project have Docker support?" in prompt
    assert "CONVERSATION HISTORY:" in prompt
    assert "Hi! How can I help you" in prompt


def test_offline_deterministic_fallback(sample_dossier):
    """When no AI provider is configured, chat falls back to deterministic fact summary."""
    analyzer = RepositoryAnalyzer()
    with patch("ai.provider.get_ai_provider", return_value=None):
        reply = analyzer.chat(dossier=sample_dossier, query="Can you tell me about this?")
        assert "[Offline Intelligence Mode]" in reply
        assert "tiangolo/fastapi" in reply
        assert "Python" in reply
        assert "Starlette" in reply
        assert "Dockerfile present" in reply


def test_ai_provider_delegation(sample_dossier):
    """When AI provider is active, analyzer.chat delegates to ai_provider.chat_with_repository."""
    mock_provider = MagicMock()
    mock_provider.chat_with_repository.return_value = "Yes, FastAPI includes official Docker support."

    analyzer = RepositoryAnalyzer()
    with patch("ai.provider.get_ai_provider", return_value=mock_provider):
        reply = analyzer.chat(dossier=sample_dossier, query="Does it have Docker?")
        assert reply == "Yes, FastAPI includes official Docker support."
        assert mock_provider.chat_with_repository.called


def test_openai_chat_with_repository(sample_dossier):
    """Verify OpenAIProvider.chat_with_repository calls completions.create with system chat prompt."""
    from ai.openai_provider import OpenAIProvider

    with patch("ai.openai_provider.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "FastAPI uses Starlette and Pydantic under the hood."
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_resp

        provider = OpenAIProvider(api_key="sk-testkey12345", model="gpt-4o-mini")
        answer = provider.chat_with_repository(sample_dossier, query="What is FastAPI built on?")

        assert "FastAPI uses Starlette and Pydantic" in answer
        assert mock_client.chat.completions.create.called
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"
        messages = call_kwargs["messages"]
        assert any("expert AI technical software architect" in m["content"] for m in messages if m["role"] == "system")
