"""Resilient, reusable GitHub REST API client for OpenSource Radar."""

import base64
import logging
import time
from typing import Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from config import get_settings
from core.cache import global_cache
from core.rate_limiter import RateLimiter

logger = logging.getLogger("opensource_radar.github")


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class GitHubAuthError(GitHubAPIError):
    """Raised when authentication fails (HTTP 401)."""
    pass


class GitHubRateLimitError(GitHubAPIError):
    """Raised when rate limit is exceeded (HTTP 403 / 429)."""
    pass


class GitHubNotFoundError(GitHubAPIError):
    """Raised when a resource is not found (HTTP 404)."""
    pass


class GitHubValidationError(GitHubAPIError):
    """Raised when a search query or input is invalid (HTTP 422)."""
    pass


_TOKEN_UNSET = object()


class GitHubClient:
    """Thread-safe, rate-limit aware GitHub REST API v3 client."""

    def __init__(
        self,
        token: Any = _TOKEN_UNSET,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self.token = settings.GITHUB_TOKEN if token is _TOKEN_UNSET else token
        self.base_url = (base_url or settings.GITHUB_API_BASE).rstrip("/")
        self.timeout = timeout or settings.GITHUB_REQUEST_TIMEOUT
        self.max_retries = max_retries or settings.GITHUB_MAX_RETRIES
        self.rate_limiter = RateLimiter()

        # Configure session with standard retries for connection/server errors
        self.session = requests.Session()
        retries = Retry(
            total=self.max_retries,
            backoff_factor=1.0,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get_headers(self, accept: str = "application/vnd.github.v3+json") -> dict[str, str]:
        """Construct secure request headers without exposing tokens in logs."""
        headers = {
            "Accept": accept,
            "User-Agent": "OpenSource-Radar/1.0",
        }
        if self.token and self.token.strip():
            # Use Bearer token authorization
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        use_cache: bool = False,
        cache_ttl: int = 300,
    ) -> dict[str, Any]:
        """Execute an HTTP request with error handling, rate limiting, and caching."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        cache_key = f"{method}:{url}:{sorted((params or {}).items())}"

        if use_cache and method.upper() == "GET":
            cached_res = global_cache.get(cache_key)
            if cached_res is not None:
                return cached_res

        req_headers = self._get_headers()
        if headers:
            req_headers.update(headers)

        # Check proactive rate limit exhaustion
        if self.rate_limiter.is_exhausted:
            wait_sec = self.rate_limiter.seconds_until_reset
            raise GitHubRateLimitError(
                f"GitHub API rate limit exhausted. Resets in {wait_sec} seconds.",
                status_code=403,
                details=self.rate_limiter.to_dict(),
            )

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=req_headers,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as exc:
            logger.error(f"GitHub request timed out for {endpoint}")
            raise GitHubAPIError(f"Request timed out connecting to GitHub API ({endpoint}).") from exc
        except requests.exceptions.ConnectionError as exc:
            logger.error(f"GitHub network connection error for {endpoint}")
            raise GitHubAPIError(f"Network error connecting to GitHub API: {str(exc)}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error(f"GitHub request failed: {str(exc)}")
            raise GitHubAPIError(f"GitHub API request failed: {str(exc)}") from exc

        # Always update rate limiter state from headers
        self.rate_limiter.update_from_headers(response.headers)

        status = response.status_code

        # Parse JSON or fallback
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {"raw_text": response.text}

        if status == 200 or status == 201:
            if use_cache and method.upper() == "GET":
                global_cache.set(cache_key, data, ttl=cache_ttl)
            return data

        # Error handling
        err_msg = data.get("message", response.reason or f"HTTP {status}")
        if status == 401:
            logger.warning("GitHub API authentication failure (401)")
            raise GitHubAuthError("Invalid or expired GitHub Personal Access Token.", status_code=401, details=data)

        if status == 403:
            if "rate limit" in err_msg.lower() or self.rate_limiter.remaining == 0:
                logger.warning("GitHub API rate limit hit (403)")
                raise GitHubRateLimitError(
                    f"GitHub API rate limit reached. Reset in {self.rate_limiter.seconds_until_reset}s.",
                    status_code=403,
                    details=self.rate_limiter.to_dict(),
                )
            raise GitHubAPIError(f"Access forbidden: {err_msg}", status_code=403, details=data)

        if status == 404:
            raise GitHubNotFoundError(f"Requested GitHub resource not found: {endpoint}", status_code=404, details=data)

        if status == 422:
            raise GitHubValidationError(f"Invalid search syntax or query parameters: {err_msg}", status_code=422, details=data)

        if status == 429:
            raise GitHubRateLimitError("Too many requests (HTTP 429). Throttled by GitHub.", status_code=429, details=data)

        raise GitHubAPIError(f"GitHub API error {status}: {err_msg}", status_code=status, details=data)

    def test_connection(self) -> dict[str, Any]:
        """Test the connection to GitHub API and retrieve identity/rate limit status."""
        try:
            if self.token and self.token.strip():
                # Authenticated user check
                user_data = self._request("GET", "user", use_cache=False)
                rate_data = self.get_rate_limit()
                return {
                    "authenticated": True,
                    "status": "connected",
                    "username": user_data.get("login"),
                    "name": user_data.get("name"),
                    "rate_limit": rate_data.get("resources", {}).get("core", self.rate_limiter.to_dict()),
                }
            else:
                # Public unauthenticated ping
                rate_data = self.get_rate_limit()
                return {
                    "authenticated": False,
                    "status": "connected_unauthenticated",
                    "username": None,
                    "rate_limit": rate_data.get("resources", {}).get("core", self.rate_limiter.to_dict()),
                    "warning": "Running unauthenticated (60 req/hr). Add GITHUB_TOKEN for 5,000 req/hr.",
                }
        except GitHubAuthError as exc:
            return {
                "authenticated": False,
                "status": "auth_failed",
                "error": str(exc),
            }
        except GitHubAPIError as exc:
            return {
                "authenticated": False,
                "status": "error",
                "error": str(exc),
            }

    def get_rate_limit(self) -> dict[str, Any]:
        """Fetch real-time rate limit metrics directly from GitHub."""
        res = self._request("GET", "rate_limit", use_cache=False)
        return res

    def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        page: int = 1,
        per_page: int = 30,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Execute a repository search with GitHub search query syntax."""
        if not query or not query.strip():
            raise GitHubValidationError("Search query cannot be empty.")

        params = {
            "q": query.strip(),
            "sort": sort,
            "order": order,
            "page": max(1, page),
            "per_page": min(100, max(1, per_page)),
        }
        return self._request("GET", "search/repositories", params=params, use_cache=use_cache, cache_ttl=300)

    def get_repository(self, owner: str, repo: str, use_cache: bool = True) -> dict[str, Any]:
        """Fetch full repository metadata."""
        if not owner or not repo:
            raise GitHubValidationError("Owner and repo name are required.")
        endpoint = f"repos/{owner.strip()}/{repo.strip()}"
        return self._request("GET", endpoint, use_cache=use_cache, cache_ttl=600)

    def get_readme(self, owner: str, repo: str, use_cache: bool = True) -> Optional[str]:
        """Fetch and decode the raw README content of a repository."""
        endpoint = f"repos/{owner.strip()}/{repo.strip()}/readme"
        try:
            data = self._request("GET", endpoint, use_cache=use_cache, cache_ttl=1800)
            content_b64 = data.get("content", "")
            if content_b64:
                return base64.b64decode(content_b64).decode("utf-8", errors="replace")
            return None
        except GitHubNotFoundError:
            return None

    def get_languages(self, owner: str, repo: str, use_cache: bool = True) -> dict[str, int]:
        """Fetch byte counts for languages used in repository."""
        endpoint = f"repos/{owner.strip()}/{repo.strip()}/languages"
        try:
            return self._request("GET", endpoint, use_cache=use_cache, cache_ttl=1800)
        except GitHubNotFoundError:
            return {}

    def get_latest_release(self, owner: str, repo: str, use_cache: bool = True) -> Optional[dict[str, Any]]:
        """Fetch metadata for latest release if published."""
        endpoint = f"repos/{owner.strip()}/{repo.strip()}/releases/latest"
        try:
            return self._request("GET", endpoint, use_cache=use_cache, cache_ttl=1800)
        except GitHubNotFoundError:
            return None

    def get_recent_commits(self, owner: str, repo: str, limit: int = 5, use_cache: bool = True) -> list[dict[str, Any]]:
        """Fetch recent commit records."""
        endpoint = f"repos/{owner.strip()}/{repo.strip()}/commits"
        params = {"per_page": min(20, max(1, limit))}
        try:
            res = self._request("GET", endpoint, params=params, use_cache=use_cache, cache_ttl=600)
            return res if isinstance(res, list) else []
        except GitHubNotFoundError:
            return []

    def get_file_tree(self, owner: str, repo: str, branch: str = "main", use_cache: bool = True) -> list[dict[str, Any]]:
        """Fetch the git tree of repository recursively."""
        endpoint = f"repos/{owner.strip()}/{repo.strip()}/git/trees/{branch}"
        params = {"recursive": "1"}
        try:
            res = self._request("GET", endpoint, params=params, use_cache=use_cache, cache_ttl=1800)
            return res.get("tree", []) if isinstance(res, dict) else []
        except (GitHubNotFoundError, GitHubAPIError):
            # Fallback for default branches like 'master'
            if branch == "main":
                try:
                    return self.get_file_tree(owner, repo, branch="master", use_cache=use_cache)
                except Exception:
                    return []
            return []

    def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        max_size_kb: int = 100,
        use_cache: bool = True,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Safely fetch and decode a text file from a repository.
        Rejects binary files and files larger than max_size_kb.
        Returns (content_text, error_message).
        """
        # Binary extension guard
        binary_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
            ".so", ".dylib", ".dll", ".exe", ".bin", ".o", ".a",
            ".pyc", ".pyd", ".wasm", ".class", ".jar",
            ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx",
            ".mp3", ".mp4", ".wav", ".avi", ".mov",
            ".ttf", ".woff", ".woff2", ".eot",
            ".db", ".sqlite", ".sqlite3",
        }
        clean_path = path.lower().strip()
        if any(clean_path.endswith(ext) for ext in binary_extensions):
            return None, "Binary file inspection rejected for security and performance."

        endpoint = f"repos/{owner.strip()}/{repo.strip()}/contents/{path.lstrip('/')}"
        try:
            data = self._request("GET", endpoint, use_cache=use_cache, cache_ttl=1800)
        except GitHubNotFoundError:
            return None, "File not found in repository."
        except GitHubAPIError as exc:
            return None, f"Failed to retrieve file: {str(exc)}"

        if isinstance(data, list):
            return None, "Path is a directory, not a file."

        size_kb = (data.get("size", 0) or 0) / 1024
        if size_kb > max_size_kb:
            return None, f"File size ({size_kb:.1f} KB) exceeds safety limit ({max_size_kb} KB)."

        content_b64 = data.get("content", "")
        if not content_b64:
            return "", None

        try:
            decoded = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            return decoded, None
        except Exception as exc:
            return None, f"Decoding error: {str(exc)}"


# Module-level singleton helper
_client_instance: Optional[GitHubClient] = None


def get_github_client(token: Any = _TOKEN_UNSET) -> GitHubClient:
    """Return the shared GitHubClient singleton."""
    global _client_instance
    if _client_instance is None or token is not _TOKEN_UNSET:
        _client_instance = GitHubClient(token=token)
    return _client_instance
