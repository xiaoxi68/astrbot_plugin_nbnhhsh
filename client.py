from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class NbnhhshClient:
    """HTTP client for the nbnhhsh API."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def startup(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def guess(self, keyword: str) -> Optional[Dict[str, Any]]:
        if not keyword:
            return None

        if self._client is None:
            await self.startup()

        assert self._client is not None
        try:
            response = await self._client.post(
                "guess",
                json={"text": keyword},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        data = response.json()
        if isinstance(data, list) and data:
            first_item = data[0]
            if isinstance(first_item, dict):
                return first_item
        return None
