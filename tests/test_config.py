"""Unit tests for application configuration and secret masking."""

import os
import pytest
from config import Settings, get_settings


def test_default_settings():
    """Verify default configuration values."""
    settings = get_settings()
    assert settings.APP_NAME == "OpenSource Radar"
    assert settings.GITHUB_API_BASE == "https://api.github.com"
    assert settings.DATABASE_URL.startswith("sqlite:///")
    assert settings.GITHUB_REQUEST_TIMEOUT >= 10


def test_secret_masking():
    """Verify that secrets are masked and never leaked in representations."""
    # Test masked token
    s1 = Settings(GITHUB_TOKEN="ghp_1234567890abcdef")
    assert s1.has_github_token is True
    assert "1234567890" not in s1.masked_github_token
    assert s1.masked_github_token.startswith("ghp_")
    assert s1.masked_github_token.endswith("def")

    # Test representation does not leak full token
    repr_str = repr(s1)
    assert "ghp_1234567890abcdef" not in repr_str
    assert s1.masked_github_token in repr_str

    # Test unconfigured
    s2 = Settings(GITHUB_TOKEN=None, OPENAI_API_KEY=None, GEMINI_API_KEY=None)
    assert s2.has_github_token is False
    assert s2.masked_github_token == "Not Configured"
    assert s2.masked_openai_key == "Not Configured"
    assert s2.masked_gemini_key == "Not Configured"


def test_sqlite_path_resolution():
    """Verify that relative sqlite paths resolve to absolute paths."""
    s = Settings(DATABASE_URL="sqlite:///data/test_custom.db")
    assert "test_custom.db" in s.DATABASE_URL
    assert os.path.isabs(s.DATABASE_URL.replace("sqlite:///", ""))
