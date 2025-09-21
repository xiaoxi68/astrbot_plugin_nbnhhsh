from __future__ import annotations

import time
from typing import Any, Dict, Optional


class TTLCache:
    """A lightweight in-memory cache with TTL and soft size limit."""

    def __init__(self, ttl_seconds: float, max_size: int = 0) -> None:
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._store: Dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        record = self._store.get(key)
        if not record:
            return None

        expires_at, value = record
        if expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        expires_at = time.monotonic() + self._ttl if self._ttl > 0 else float("inf")
        self._store[key] = (expires_at, value)
        self._enforce_limits()

    def clear(self) -> None:
        self._store.clear()

    def _enforce_limits(self) -> None:
        if self._max_size and len(self._store) > self._max_size:
            self.cleanup()
            while len(self._store) > self._max_size:
                # Remove the oldest entry by expiry
                oldest_key = min(self._store.items(), key=lambda item: item[1][0])[0]
                self._store.pop(oldest_key, None)

    def cleanup(self) -> None:
        """Remove expired items proactively."""
        now = time.monotonic()
        expired_keys = [key for key, (expires_at, _) in self._store.items() if expires_at < now]
        for key in expired_keys:
            self._store.pop(key, None)
