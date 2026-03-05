from __future__ import annotations
import logging
from typing import Any
import httpx
from .config import config

log = logging.getLogger(__name__)


class RLMClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or config.RLM_URL
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10)

    async def _rpc(self, method: str, params: dict[str, Any]) -> Any:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        try:
            resp = await self._client.post("/mcp", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result")
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
            log.warning("RLM unreachable: %s", e)
            return None

    async def search_facts(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        result = await self._rpc("rlm_search_facts", {"query": query, "top_k": top_k})
        return result or []

    async def add_fact(self, content: str, level: str = "project", domain: str = "") -> dict[str, Any]:
        result = await self._rpc("rlm_add_fact", {"content": content, "level": level, "domain": domain})
        return result or {}

    async def route_context(self, query: str) -> dict[str, Any]:
        result = await self._rpc("rlm_route_context", {"query": query})
        return result or {}

    async def start_session(self) -> dict[str, Any]:
        result = await self._rpc("rlm_start_session", {})
        return result or {}

    async def sync_state(self, state: dict[str, Any]) -> dict[str, Any]:
        result = await self._rpc("rlm_sync_state", {"state": state})
        return result or {}

    async def close(self) -> None:
        await self._client.aclose()
