"""Shared pytest fixtures.

We don't have a real GigaChat / Qdrant in CI, so by default they are mocked.
Set RUN_INTEGRATION=1 to skip mocking and hit the real services (requires .env).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure backend is on sys.path
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-long-enough-12345")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql+psycopg2://x:x@localhost/x")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")


@pytest.fixture
def fake_gigachat(monkeypatch):
    """Replace the GigaChat singleton with a fresh mock per test."""
    from app.services import gigachat as gc
    from app.rag import orchestrator as orch

    mock = MagicMock()
    mock.embed = AsyncMock(return_value=[[0.1] * 1024])
    mock.chat_completion = AsyncMock(
        return_value={
            "choices": [
                {
                    "message": {
                        "content": (
                            "Краткий ответ: грант «Агростартап» предоставляется "
                            "начинающим фермерам [1]. Размер — до 5 млн ₽ [1]."
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }
    )
    mock.close = AsyncMock()
    monkeypatch.setattr(gc, "_client", mock, raising=False)
    monkeypatch.setattr(gc, "get_gigachat", lambda: mock)
    monkeypatch.setattr(orch, "get_gigachat", lambda: mock)
    return mock


@pytest.fixture
def fake_qdrant(monkeypatch):
    """Replace the Qdrant singleton with a fresh mock per test."""
    from app.services import qdrant_service as qs
    from app.rag import orchestrator as orch

    default_hits = [
        {
            "chunk_id": "00000000-0000-0000-0000-000000000001",
            "score": 0.92,
            "payload": {
                "document_id": "11111111-1111-1111-1111-111111111111",
                "title": "Приказ Минсельхоза о грантах «Агростартап»",
                "short_title": "Агростартап",
                "doc_number": "Прик. 26",
                "section_path": "Раздел II / пункт 5",
                "content": (
                    "Грант «Агростартап» предоставляется главам крестьянских "
                    "(фермерских) хозяйств в размере до 5 млн рублей на цели "
                    "создания и развития хозяйства."
                ),
                "is_active": True,
                "source_url": "http://example.gov.ru/agrostart",
            },
        }
    ]

    mock = MagicMock()
    mock.search = AsyncMock(return_value=default_hits)
    mock.upsert_chunks = AsyncMock()
    mock.delete_by_document = AsyncMock()
    mock.ensure_collection = AsyncMock()
    mock.close = AsyncMock()

    async def _factory() -> Any:
        return mock

    monkeypatch.setattr(qs, "_qdrant", mock, raising=False)
    monkeypatch.setattr(qs, "get_qdrant", _factory)
    monkeypatch.setattr(orch, "get_qdrant", _factory)
    return mock


@pytest.fixture
def fake_cache(monkeypatch):
    """Disable cache per test to keep things deterministic."""
    from app.services import cache as c
    from app.rag import orchestrator as orch

    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.close = AsyncMock()
    monkeypatch.setattr(c, "_cache", mock, raising=False)
    monkeypatch.setattr(c, "get_cache", lambda: mock)
    monkeypatch.setattr(orch, "get_cache", lambda: mock)
    return mock
