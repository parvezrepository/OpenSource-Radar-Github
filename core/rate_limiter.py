"""Rate limit tracking and throttling guard for GitHub API."""

import time
from typing import Any, Mapping, Optional


class RateLimiter:
    """Tracks and evaluates GitHub API rate limits from response headers."""

    def __init__(self) -> None:
        self.limit: int = 60  # Default unauthenticated limit
        self.remaining: int = 60
        self.reset_timestamp: int = int(time.time()) + 3600
        self.resource: str = "core"
        self.last_updated: float = time.time()

    def update_from_headers(self, headers: Mapping[str, Any]) -> None:
        """Update rate limit metrics from HTTP response headers (case-insensitive)."""
        lower_headers = {k.lower(): v for k, v in headers.items()}
        if "x-ratelimit-limit" in lower_headers:
            try:
                self.limit = int(lower_headers["x-ratelimit-limit"])
            except ValueError:
                pass

        if "x-ratelimit-remaining" in lower_headers:
            try:
                self.remaining = int(lower_headers["x-ratelimit-remaining"])
            except ValueError:
                pass

        if "x-ratelimit-reset" in lower_headers:
            try:
                self.reset_timestamp = int(lower_headers["x-ratelimit-reset"])
            except ValueError:
                pass

        if "x-ratelimit-resource" in lower_headers:
            self.resource = str(lower_headers["x-ratelimit-resource"])

        self.last_updated = time.time()

    @property
    def seconds_until_reset(self) -> int:
        """Return the number of seconds until the rate limit resets."""
        now = int(time.time())
        return max(0, self.reset_timestamp - now)

    @property
    def is_exhausted(self) -> bool:
        """Return True if rate limit is exhausted and reset time is in the future."""
        return self.remaining <= 0 and self.seconds_until_reset > 0

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation of current rate limit state."""
        return {
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_timestamp": self.reset_timestamp,
            "seconds_until_reset": self.seconds_until_reset,
            "resource": self.resource,
            "is_exhausted": self.is_exhausted,
            "percent_remaining": round((self.remaining / max(1, self.limit)) * 100, 1),
        }
