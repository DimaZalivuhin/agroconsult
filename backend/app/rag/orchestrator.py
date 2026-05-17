"""RAG orchestrator — main consultation pipeline.

Pipeline stages (MVP):
1. Preprocess query (normalise, derive profile filters).
2. Embed query via GigaChat embeddings.
3. Dense retrieval from Qdrant with metadata filters.
4. Assemble context (top-K with token budget).
5. Generate answer via GigaChat with structured citation prompt.
6. Post-process (validate citations, prepare sources for UI).
7. Return AnswerResponse with sources and metrics.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.chunker import count_tokens
from app.rag.prompts import SYSTEM_PROMPT, build_user_prompt, profile_to_text
from app.services.cache import get_cache, make_cache_key
from app.services.gigachat import get_gigachat
from app.services.qdrant_service import get_qdrant

log = get_logger("rag")

_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


@dataclass(slots=True)
class RagResult:
    answer: str
    sources: list[dict]
    token_usage: dict = field(default_factory=dict)
    retrieval_meta: dict = field(default_factory=dict)


def _profile_filters(profile: dict | None) -> dict[str, Any]:
    """Derive Qdrant payload filters from a farmer profile.

    Region filter is intentionally not strict: we surface federal measures
    plus those that explicitly target the user's region. The "OR with absence"
    is approximated by not filtering at all on regions — federal measures have
    empty target_regions arrays and pass through any positive match too.
    Practical recall > strict precision at this stage.
    """
    if not profile:
        return {}
    # We keep filters minimal to avoid over-narrowing on a small corpus.
    # Profile fields are added to the LLM prompt so the model can reason about
    # relevance, even when not used as hard filters.
    return {}


async def _embed_query(question: str) -> list[float]:
    giga = get_gigachat()
    vectors = await giga.embed([question])
    return vectors[0]


async def _retrieve(
    question: str,
    *,
    profile: dict | None,
    top_k: int,
) -> tuple[list[dict], dict]:
    """Run dense retrieval and return (hits, metrics)."""
    started = time.perf_counter()
    vector = await _embed_query(question)
    embed_ms = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    qdrant = await get_qdrant()
    hits = await qdrant.search(
        vector,
        top_k=top_k,
        filters=_profile_filters(profile),
    )
    search_ms = (time.perf_counter() - started) * 1000

    meta = {
        "embed_ms": round(embed_ms, 1),
        "search_ms": round(search_ms, 1),
        "n_candidates": len(hits),
    }
    return hits, meta


def _assemble_context(
    hits: list[dict],
    *,
    top_k: int,
    max_tokens: int,
) -> tuple[list[dict], list[dict]]:
    """Select top-K hits within a token budget.

    Returns (context_blocks_for_prompt, sources_for_response).
    """
    context_blocks: list[dict] = []
    sources_for_response: list[dict] = []
    used_tokens = 0

    for hit in hits[:top_k]:
        payload = hit["payload"]
        content = payload.get("content") or ""
        chunk_tokens = count_tokens(content)
        if used_tokens + chunk_tokens > max_tokens and context_blocks:
            break

        block = {
            "content": content,
            "title": payload.get("title"),
            "short_title": payload.get("short_title"),
            "doc_number": payload.get("doc_number"),
            "section_path": payload.get("section_path"),
        }
        context_blocks.append(block)

        sources_for_response.append(
            {
                "chunk_id": hit["chunk_id"],
                "document_id": payload.get("document_id"),
                "title": payload.get("title") or "",
                "short_title": payload.get("short_title"),
                "doc_number": payload.get("doc_number"),
                "section_path": payload.get("section_path"),
                "snippet": (content[:280] + "…") if len(content) > 280 else content,
                "score": hit["score"],
                "source_url": payload.get("source_url"),
            }
        )
        used_tokens += chunk_tokens

    return context_blocks, sources_for_response


def _filter_cited_sources(answer: str, all_sources: list[dict]) -> list[dict]:
    """Keep only sources actually referenced in the answer.

    If the model didn't cite anything, keep top-3 by score so the UI still
    surfaces something to the user.
    """
    cited_indices = {int(m.group(1)) for m in _CITATION_PATTERN.finditer(answer)}
    if not cited_indices:
        return all_sources[:3]
    # Citations are 1-based; map to 0-based and clip to available range
    selected = []
    for idx in sorted(cited_indices):
        i = idx - 1
        if 0 <= i < len(all_sources):
            selected.append(all_sources[i])
    return selected or all_sources[:3]


async def answer_question(
    question: str,
    *,
    profile: Optional[dict] = None,
    top_k_retrieval: Optional[int] = None,
    top_k_context: Optional[int] = None,
    use_cache: bool = True,
) -> RagResult:
    """Main entry point. Returns a RagResult ready to be persisted and returned."""
    top_k_retrieval = top_k_retrieval or settings.rag_top_k_retrieval
    top_k_context = top_k_context or settings.rag_top_k_context

    cache = get_cache()
    cache_key = make_cache_key(
        "answer",
        question.lower().strip(),
        (profile or {}).get("region_code"),
        (profile or {}).get("farm_type"),
        (profile or {}).get("direction"),
    )

    if use_cache:
        cached = await cache.get(cache_key)
        if cached:
            log.info(f"Cache HIT for question: {question[:60]}")
            return RagResult(**cached)

    overall_start = time.perf_counter()
    hits, retrieval_meta = await _retrieve(
        question, profile=profile, top_k=top_k_retrieval
    )

    if not hits:
        result = RagResult(
            answer=(
                "По вашему запросу не удалось найти подходящих нормативных документов "
                "в базе знаний. Попробуйте переформулировать вопрос или уточнить "
                "интересующую вас меру поддержки."
            ),
            sources=[],
            retrieval_meta=retrieval_meta | {"total_ms": round((time.perf_counter() - overall_start) * 1000, 1)},
        )
        return result

    context_blocks, all_sources = _assemble_context(
        hits,
        top_k=top_k_context,
        max_tokens=settings.rag_max_context_tokens,
    )

    profile_summary = profile_to_text(profile)
    user_prompt = build_user_prompt(question, profile_summary, context_blocks)

    giga = get_gigachat()
    gen_start = time.perf_counter()
    completion = await giga.chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=settings.rag_temperature,
        max_tokens=1500,
    )
    gen_ms = (time.perf_counter() - gen_start) * 1000

    answer = completion["choices"][0]["message"]["content"].strip()
    usage = completion.get("usage", {})

    cited_sources = _filter_cited_sources(answer, all_sources)

    retrieval_meta.update(
        {
            "gen_ms": round(gen_ms, 1),
            "total_ms": round((time.perf_counter() - overall_start) * 1000, 1),
            "n_context_blocks": len(context_blocks),
            "n_cited": len(cited_sources),
        }
    )

    result = RagResult(
        answer=answer,
        sources=cited_sources,
        token_usage=usage,
        retrieval_meta=retrieval_meta,
    )

    if use_cache:
        await cache.set(
            cache_key,
            {
                "answer": result.answer,
                "sources": result.sources,
                "token_usage": result.token_usage,
                "retrieval_meta": result.retrieval_meta,
            },
            ttl=settings.redis_cache_ttl,
        )

    return result
