"""Unit tests for RepositoryAnalyzer, static dependency parsing, and safe file inspection."""

from unittest.mock import MagicMock
import pytest

from core.github_client import GitHubClient
from core.repository_analyzer import RepositoryAnalyzer


def test_readme_parsing_sections():
    """Verify markdown header regex correctly extracts structured sections."""
    sample_readme = """
    # Sample Project
    This is an awesome open-source project.
    
    ## Why Sample Project
    We built this to solve high-frequency latency issues in distributed trading.
    
    ## Features
    - Ultra-low latency engine
    - Support for multiple protocols
    
    ## Installation
    ```bash
    pip install sample-project
    ```
    
    ## Usage
    ```python
    import sample
    sample.run()
    ```
    
    ## Limitations
    Does not support Windows 32-bit.
    """
    sections = RepositoryAnalyzer.parse_readme_sections(sample_readme)
    assert "solve high-frequency latency" in sections["problem_solved"]
    assert "Ultra-low latency" in sections["features"]
    assert "pip install" in sections["installation"]
    assert "sample.run()" in sections["usage"]
    assert "Windows 32-bit" in sections["limitations"]


def test_missing_documentation_handling():
    """Verify graceful handling when README is missing or empty."""
    sections_none = RepositoryAnalyzer.parse_readme_sections(None)
    assert "No README documentation" in sections_none["overview"]
    assert "Not specified" in sections_none["problem_solved"]

    sections_empty = RepositoryAnalyzer.parse_readme_sections("   ")
    assert "No README documentation" in sections_empty["overview"]


def test_manifest_dependency_parsing():
    """Verify static extraction of dependencies without executing code."""
    # Test requirements.txt
    reqs = "fastapi>=0.100.0\npytest\n# Comment\npandas==2.2.0\nrequests"
    parsed_reqs = RepositoryAnalyzer.parse_manifest_dependencies("requirements.txt", reqs)
    assert "fastapi" in parsed_reqs
    assert "pytest" in parsed_reqs
    assert "pandas" in parsed_reqs
    assert "requests" in parsed_reqs

    # Test package.json
    pkg_json = '{\n  "dependencies": {\n    "express": "^4.18.2",\n    "react": "^18.2.0"\n  }\n}'
    parsed_pkg = RepositoryAnalyzer.parse_manifest_dependencies("package.json", pkg_json)
    assert "express" in parsed_pkg
    assert "react" in parsed_pkg


def test_binary_file_rejection():
    """Verify binary files are rejected immediately by extension without downloading content."""
    client = GitHubClient()
    
    # Test various binary extensions
    binaries = ["model.bin", "image.png", "lib.so", "archive.zip", "compiled.dll", "bytecode.pyc"]
    for b_path in binaries:
        content, err = client.get_file_content("owner", "repo", b_path)
        assert content is None
        assert "binary file inspection rejected" in err.lower()


def test_file_size_limit_guard():
    """Verify files exceeding max_size_kb are rejected safely."""
    mock_client = MagicMock(spec=GitHubClient)
    # Return 150KB file
    mock_client._request.return_value = {
        "size": 150 * 1024,
        "content": "",
    }
    mock_client.get_file_content = GitHubClient.get_file_content.__get__(mock_client, GitHubClient)

    content, err = mock_client.get_file_content("owner", "repo", "big_data.csv", max_size_kb=100)
    assert content is None
    assert "exceeds safety limit" in err.lower()
