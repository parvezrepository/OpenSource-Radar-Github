"""Unit tests for GitHubClient, RateLimiter, and error handling."""

from unittest.mock import MagicMock, patch
import pytest
import requests

from core.github_client import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubClient,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubValidationError,
)
from core.rate_limiter import RateLimiter


def test_rate_limiter_parsing():
    """Verify rate limiter extracts headers accurately."""
    limiter = RateLimiter()
    headers = {
        "x-ratelimit-limit": "5000",
        "x-ratelimit-remaining": "4800",
        "x-ratelimit-reset": "1999999999",
        "x-ratelimit-resource": "core",
    }
    limiter.update_from_headers(headers)
    assert limiter.limit == 5000
    assert limiter.remaining == 4800
    assert limiter.reset_timestamp == 1999999999
    assert limiter.is_exhausted is False
    assert limiter.to_dict()["percent_remaining"] == 96.0


def test_client_headers_without_token():
    """Verify headers for unauthenticated requests."""
    client = GitHubClient(token=None)
    headers = client._get_headers()
    assert "Authorization" not in headers
    assert "User-Agent" in headers


def test_client_headers_with_token():
    """Verify headers format Bearer token correctly."""
    client = GitHubClient(token="secret_token_123")
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer secret_token_123"


@patch.object(requests.Session, "request")
def test_github_auth_error_401(mock_request):
    """Verify 401 status triggers GitHubAuthError on direct call and returns auth_failed on test_connection."""
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {"x-ratelimit-remaining": "60"}
    mock_resp.content = b'{"message": "Bad credentials"}'
    mock_resp.json.return_value = {"message": "Bad credentials"}
    mock_request.return_value = mock_resp

    client = GitHubClient(token="invalid_token")
    with pytest.raises(GitHubAuthError):
        client._request("GET", "user")

    # test_connection catches GitHubAuthError and returns a structured response
    conn_result = client.test_connection()
    assert conn_result["status"] == "auth_failed"
    assert conn_result["authenticated"] is False


@patch.object(requests.Session, "request")
def test_github_rate_limit_error_403(mock_request):
    """Verify rate limit exceeded 403 triggers GitHubRateLimitError."""
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {
        "x-ratelimit-remaining": "0",
        "x-ratelimit-limit": "60",
        "x-ratelimit-reset": "2000000000",
    }
    mock_resp.content = b'{"message": "API rate limit exceeded"}'
    mock_resp.json.return_value = {"message": "API rate limit exceeded"}
    mock_request.return_value = mock_resp

    client = GitHubClient(token=None)
    with pytest.raises(GitHubRateLimitError):
        client.get_repository("owner", "repo")


@patch.object(requests.Session, "request")
def test_github_not_found_404(mock_request):
    """Verify 404 resource missing triggers GitHubNotFoundError."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.headers = {}
    mock_resp.content = b'{"message": "Not Found"}'
    mock_resp.json.return_value = {"message": "Not Found"}
    mock_request.return_value = mock_resp

    client = GitHubClient()
    with pytest.raises(GitHubNotFoundError):
        client.get_repository("nonexistent", "repo")


@patch.object(requests.Session, "request")
def test_github_timeout_handling(mock_request):
    """Verify network timeouts raise GitHubAPIError with informative message."""
    mock_request.side_effect = requests.exceptions.Timeout("Connection timed out")

    client = GitHubClient()
    with pytest.raises(GitHubAPIError) as exc_info:
        client.get_repository("owner", "repo")
    assert "timed out" in str(exc_info.value).lower()
