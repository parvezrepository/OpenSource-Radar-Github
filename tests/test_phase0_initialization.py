"""Phase 0 Initialization and Architecture Verification Tests."""

from pathlib import Path
import sys


def test_python_version():
    """Verify Python version is 3.11 or greater."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, found {sys.version}"


def test_core_directories_exist():
    """Verify that all mandatory project directories exist."""
    root = Path(__file__).parent.parent
    expected_dirs = [
        "pages",
        "core",
        "ai",
        "database",
        "services",
        "utils",
        "data",
        "logs",
        "tests",
    ]
    for d in expected_dirs:
        dir_path = root / d
        assert dir_path.is_dir(), f"Expected directory '{d}' does not exist."


def test_mandatory_memory_files_exist():
    """Verify that all 7 mandatory project memory files exist and are not empty."""
    root = Path(__file__).parent.parent
    memory_files = [
        "PROJECT_CONTEXT.md",
        "IMPLEMENTATION_PLAN.md",
        "ARCHITECTURE.md",
        "DECISIONS.md",
        "CHANGELOG.md",
        "TEST_REPORT.md",
        "CURRENT_STATUS.md",
    ]
    for filename in memory_files:
        file_path = root / filename
        assert file_path.is_file(), f"Memory file '{filename}' is missing."
        assert file_path.stat().st_size > 50, f"Memory file '{filename}' is empty or too short."


def test_configuration_and_docs_exist():
    """Verify requirements.txt, .env.example, .gitignore, and README.md exist."""
    root = Path(__file__).parent.parent
    core_files = [
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
    ]
    for filename in core_files:
        file_path = root / filename
        assert file_path.is_file(), f"Core file '{filename}' is missing."
        assert file_path.stat().st_size > 20, f"Core file '{filename}' is empty."


def test_no_secrets_in_env_example():
    """Verify .env.example does not contain hardcoded live API keys."""
    root = Path(__file__).parent.parent
    env_example = root / ".env.example"
    content = env_example.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("GITHUB_TOKEN=") or line.startswith("OPENAI_API_KEY=") or line.startswith("GEMINI_API_KEY="):
            val = line.split("=", 1)[1].strip()
            assert val == "", f"Secret key value committed in .env.example: {line}"


def test_core_library_imports():
    """Verify that core approved libraries can be successfully imported."""
    import streamlit
    import sqlalchemy
    import plotly
    import apscheduler
    import openai
    import google.generativeai
    import pydantic
    import httpx
    import requests
    import pandas
    import numpy

    assert streamlit.__name__ == "streamlit"
    assert sqlalchemy.__name__ == "sqlalchemy"
    assert plotly.__name__ == "plotly"
    assert apscheduler.__name__ == "apscheduler"
    assert openai.__name__ == "openai"
    assert google.generativeai.__name__ == "google.generativeai"
    assert pydantic.__name__ == "pydantic"
    assert httpx.__name__ == "httpx"
    assert requests.__name__ == "requests"
    assert pandas.__name__ == "pandas"
    assert numpy.__name__ == "numpy"
