from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .cache import TTLCache
from .client import NbnhhshClient


@dataclass(slots=True)
class NbnhhshResult:
    keyword: str
    translations: List[str]
    raw: Dict[str, Any]


class NbnhhshService:
    def __init__(self, client: NbnhhshClient, cache: TTLCache, logger) -> None:
        self._client = client
        self._cache = cache
        self._logger = logger

    async def lookup(self, keyword: str) -> Optional[NbnhhshResult]:
        normalized = keyword.strip()
        if not normalized:
            return None

        cache_key = normalized.lower()
        cached = self._cache.get(cache_key)
        if isinstance(cached, NbnhhshResult):
            self._logger.debug("nbnhhsh cache hit for %s", normalized)
            return cached

        payload = await self._client.guess(normalized)
        if not payload:
            self._logger.debug("nbnhhsh miss or error for %s", normalized)
            return None

        name = str(payload.get("name") or normalized)
        translations = [str(item).strip() for item in payload.get("trans", []) if str(item).strip()]

        result = NbnhhshResult(keyword=name, translations=translations, raw=payload)
        self._cache.set(cache_key, result)
        return result

    def clear_cache(self) -> None:
        self._cache.clear()
