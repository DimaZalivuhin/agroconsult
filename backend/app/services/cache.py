"""Tiny wrapper over Upstash REST Redis for response caching.

Falls back to a no-op cache when credentials are missing — useful for local
development without Upstash credentials.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("cache")


class _NoopCache:
    async def get(self, key: str) -> Optional[Any]:  # noqa: ARG002
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:  # noqa: ARG002
        return None

    async def close(self) -> None:
        return None


class UpstashCache:
    """REST client for Upstash Redis. JSON values, TTL in seconds."""

    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self._http = httpx.AsyncClient(
            timeout=10.0,
            headers={"Authorization": f"Bearer {token}"},
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def get(self, key: str) -> Optional[Any]:
        try:
            resp = await self._http.get(f"{self.url}/get/{key}")
            resp.raise_for_status()
            raw = resp.json().get("result")
            if raw is None:
                return None
            try:
                return json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                return raw
        except Exception as e:  # noqa: BLE001
            log.warning(f"Cache GET failed for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        try:
            payload = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
            params = []
            if ttl:
                params.extend(["EX", str(ttl)])
            resp = await self._http.post(
                f"{self.url}/set/{key}", json=[payload, *params]
            )
            resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            log.warning(f"Cache SET failed for {key}: {e}")


_cache: UpstashCache | _NoopCache | None = None


def get_cache():
    global _cache
    if _cache is not None:
        return _cache
    if settings.upstash_redis_url and settings.upstash_redis_token:
        _cache = UpstashCache(settings.upstash_redis_url, settings.upstash_redis_token)
    else:
        log.info("Upstash credentials not configured — using no-op cache")
        _cache = _NoopCache()
    return _cache


def make_cache_key(prefix: str, *parts: Any) -> str:
    """Stable hashed cache key."""
    payload = "|".join(str(p) for p in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{digest}"
