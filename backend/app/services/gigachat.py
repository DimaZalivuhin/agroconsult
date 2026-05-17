"""Asynchronous client for Sber GigaChat API.

Handles OAuth token caching, chat completions (streaming + non-streaming) and
embeddings. Designed to be created once per process.
"""
from __future__ import annotations

import asyncio
import time
import urllib3
import uuid
from typing import AsyncIterator, Optional

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("gigachat")

# Silence urllib3 warning when GIGACHAT_VERIFY_SSL=false. We accept this risk
# explicitly because Sber's Russian Trusted Root CA isn't in default Linux
# trust stores, and we only call known Sber endpoints.
if not settings.gigachat_verify_ssl:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GigaChatError(RuntimeError):
    """Wrapper for any GigaChat API failure."""


class GigaChatClient:
    """Async client for GigaChat.

    Token refresh is lazy — we fetch a new one once the cached token is close
    to expiry. Retries are handled per-request with exponential backoff.
    """

    def __init__(
        self,
        auth_key: Optional[str] = None,
        scope: Optional[str] = None,
        base_url: Optional[str] = None,
        auth_url: Optional[str] = None,
    ) -> None:
        self.auth_key = auth_key or settings.gigachat_auth_key or ""
        self.scope = scope or settings.gigachat_scope
        self.base_url = (base_url or settings.gigachat_base_url).rstrip("/")
        self.auth_url = auth_url or settings.gigachat_auth_url

        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

        # GigaChat uses Russian Trusted Root CA (Минцифры). On Linux images
        # without this cert in the trust store, OAuth fails with
        # "self-signed certificate in certificate chain". Configurable via env.
        self._client = httpx.AsyncClient(
            timeout=60.0,
            verify=settings.gigachat_verify_ssl,
        )

    async def close(self) -> None:
        await self._client.aclose()

    # ---------- Auth ----------
    async def _ensure_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        now = time.time()
        if self._token and now < self._token_expires_at - 30:
            return self._token

        async with self._lock:
            now = time.time()
            if self._token and now < self._token_expires_at - 30:
                return self._token

            if not self.auth_key:
                raise GigaChatError(
                    "GIGACHAT_AUTH_KEY is not configured. "
                    "Set it to base64(client_id:client_secret)."
                )

            headers = {
                "Authorization": f"Basic {self.auth_key}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
            data = {"scope": self.scope}

            try:
                resp = await self._client.post(self.auth_url, headers=headers, data=data)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                log.error(f"GigaChat OAuth failed: {e}")
                raise GigaChatError(f"OAuth failed: {e}") from e

            payload = resp.json()
            self._token = payload["access_token"]
            # expires_at returned in milliseconds since epoch
            self._token_expires_at = payload.get("expires_at", 0) / 1000.0
            if self._token_expires_at <= now:
                # Fallback: assume 30 minutes
                self._token_expires_at = now + 30 * 60

            log.info(f"GigaChat token refreshed, expires at {self._token_expires_at:.0f}")
            return self._token  # type: ignore[return-value]

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        """Authenticated request with retries on transient errors."""
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((httpx.HTTPError, GigaChatError)),
            reraise=True,
        ):
            with attempt:
                token = await self._ensure_token()
                headers = kwargs.pop("headers", {}) or {}
                headers["Authorization"] = f"Bearer {token}"
                headers.setdefault("Accept", "application/json")
                url = f"{self.base_url}{path}"
                resp = await self._client.request(method, url, headers=headers, **kwargs)
                if resp.status_code == 401:
                    # Force token refresh on next iteration
                    self._token = None
                    raise GigaChatError("401 from GigaChat — token expired")
                resp.raise_for_status()
                return resp
        raise GigaChatError("unreachable")  # pragma: no cover

    # ---------- Chat ----------
    async def chat_completion(
        self,
        messages: list[dict],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1500,
    ) -> dict:
        """Single chat completion request, returns the parsed JSON."""
        body = {
            "model": model or settings.gigachat_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.rag_temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        resp = await self._request("POST", "/chat/completions", json=body)
        return resp.json()

    async def chat_completion_stream(
        self,
        messages: list[dict],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1500,
    ) -> AsyncIterator[str]:
        """Stream tokens for an SSE-style response."""
        body = {
            "model": model or settings.gigachat_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.rag_temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        token = await self._ensure_token()
        headers = {"Authorization": f"Bearer {token}", "Accept": "text/event-stream"}
        async with self._client.stream(
            "POST", f"{self.base_url}/chat/completions", json=body, headers=headers
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    chunk = line[len("data: ") :].strip()
                    if chunk == "[DONE]":
                        break
                    yield chunk

    # ---------- Embeddings ----------
    async def embed(self, inputs: list[str], *, model: Optional[str] = None) -> list[list[float]]:
        """Return embedding vectors for the given input texts.

        We always send each text in its OWN request to GigaChat /embeddings.
        Sending multiple inputs in one request hits the 413 Payload Too Large
        limit unpredictably (the limit is per-request, not per-input). Doing
        them sequentially is slower but bulletproof — and on PERS scope it's
        also single-threaded anyway, so there's no parallelism to lose.
        """
        if not inputs:
            return []
        chosen_model = model or settings.gigachat_embeddings_model
        results: list[list[float]] = []
        for text in inputs:
            # Belt-and-suspenders: if a single chunk is still gigantic (e.g.
            # paragraph with no sentence breaks), hard-truncate to ~2000 chars
            # so we never even try to send a guaranteed-413 payload. 2000 chars
            # of Russian ≈ 700-800 tokens, well below GigaChat's ~514 limit
            # combined with JSON overhead being safe.
            safe_text = text if len(text) <= 1800 else text[:1800]
            body = {"model": chosen_model, "input": [safe_text]}
            resp = await self._request("POST", "/embeddings", json=body)
            data = resp.json()
            results.append(data["data"][0]["embedding"])
        return results


# Singleton instance used by services
_client: Optional[GigaChatClient] = None


def get_gigachat() -> GigaChatClient:
    """Return process-wide GigaChat client."""
    global _client
    if _client is None:
        _client = GigaChatClient()
    return _client
