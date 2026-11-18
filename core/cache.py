"""Lightweight in-memory TTL cache for API requests and expensive calls."""

import time
from typing import Any, Optional


class SimpleTTLCache:
    """Thread-safe in-memory cache with time-to-live expiration."""

    def __init__(self, default_ttl: int = 300, max_size: int = 500) -> None:
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if key exists and has not expired."""
        if key not in self._store:
            return None
        expires_at, value = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value with expiration timestamp."""
        ttl = ttl if ttl is not None else self.default_ttl
        # Prune oldest if capacity exceeded
        if len(self._store) >= self.max_size and key not in self._store:
            oldest_key = min(self._store, key=lambda k: self._store[k][0])
            del self._store[oldest_key]
        self._store[key] = (time.time() + ttl, value)

    def delete(self, key: str) -> bool:
        """Remove an entry from the cache."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all entries."""
        self._store.clear()

    def size(self) -> int:
        """Return count of active, unexpired entries."""
        now = time.time()
        # Clean expired
        expired = [k for k, (exp, _) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        return len(self._store)


# Global module-level cache instance
global_cache = SimpleTTLCache(default_ttl=600, max_size=1000)
