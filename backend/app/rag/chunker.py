"""Sliding-window chunker with paragraph awareness and token counting."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import tiktoken

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.parser import detect_section_path, iter_paragraphs

log = get_logger("chunker")

# tiktoken doesn't have a Russian-optimised tokeniser, but cl100k_base is a
# reasonable proxy for token counts when targeting GigaChat or OpenAI models.
# The encoder is loaded lazily because tiktoken downloads BPE files on first use.
# If the download fails (offline / restricted egress), we fall back to a simple
# char-based estimator so the system stays usable.
_ENC = None
_USE_FALLBACK = False


def _get_encoder():
    global _ENC, _USE_FALLBACK
    if _ENC is not None or _USE_FALLBACK:
        return _ENC
    try:
        _ENC = tiktoken.get_encoding("cl100k_base")
    except Exception as e:  # noqa: BLE001
        log.warning(f"Failed to load tiktoken cl100k_base, using char-based fallback: {e}")
        _USE_FALLBACK = True
        _ENC = None
    return _ENC


def _fallback_encode(text: str) -> list[int]:
    """Cheap fallback: roughly 4 chars per token (English-biased; for Russian closer to 2.5)."""
    return list(range(max(1, len(text) // 3)))


def count_tokens(text: str) -> int:
    enc = _get_encoder()
    if enc is None:
        return len(_fallback_encode(text))
    return len(enc.encode(text))


@dataclass(slots=True)
class Chunk:
    index: int
    content: str
    token_count: int
    section_path: str | None


def chunk_text(
    text: str,
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """Split text into ~chunk_size token chunks with overlap.

    Paragraphs are kept intact when they fit; long paragraphs are split by
    sentences inside the budget. Each chunk gets a best-effort section path.
    """
    target = chunk_size or settings.rag_chunk_size
    overlap_tokens = overlap or settings.rag_chunk_overlap
    assert overlap_tokens < target, "overlap must be smaller than chunk size"

    paragraphs = list(iter_paragraphs(text))
    if not paragraphs:
        return []

    chunks: list[Chunk] = []
    buffer: list[str] = []
    buffer_tokens = 0
    idx = 0

    def flush() -> None:
        nonlocal buffer, buffer_tokens, idx
        if not buffer:
            return
        content = "\n\n".join(buffer).strip()
        if not content:
            buffer = []
            buffer_tokens = 0
            return
        chunks.append(
            Chunk(
                index=idx,
                content=content,
                token_count=buffer_tokens,
                section_path=detect_section_path(content),
            )
        )
        idx += 1
        # Build new buffer from tail tokens for overlap
        if overlap_tokens > 0:
            tail = _tail_for_overlap(content, overlap_tokens)
            buffer = [tail] if tail else []
            buffer_tokens = count_tokens(tail) if tail else 0
        else:
            buffer = []
            buffer_tokens = 0

    for para in paragraphs:
        pt = count_tokens(para)
        if pt > target:
            # Long paragraph: flush existing buffer, then split by sentences
            flush()
            for sub in _split_long_paragraph(para, target):
                st = count_tokens(sub)
                if buffer_tokens + st > target and buffer:
                    flush()
                buffer.append(sub)
                buffer_tokens += st
            flush()
            continue

        if buffer_tokens + pt > target and buffer:
            flush()
        buffer.append(para)
        buffer_tokens += pt

    flush()
    return chunks


def _tail_for_overlap(text: str, overlap_tokens: int) -> str:
    enc = _get_encoder()
    if enc is None:
        # Char-based fallback: ~3 chars per token
        char_budget = overlap_tokens * 3
        return text[-char_budget:] if len(text) > char_budget else text
    tokens = enc.encode(text)
    if len(tokens) <= overlap_tokens:
        return text
    tail = tokens[-overlap_tokens:]
    return enc.decode(tail)


def _split_long_paragraph(paragraph: str, target: int) -> Iterable[str]:
    """Split a long paragraph by sentences without exceeding target tokens."""
    # Naive sentence split — good enough for НПА prose with explicit punctuation
    sentences = []
    current = []
    for token in paragraph.replace("\n", " ").split(" "):
        current.append(token)
        if token.endswith((".", "!", "?")) and len(current) > 3:
            sentences.append(" ".join(current))
            current = []
    if current:
        sentences.append(" ".join(current))

    bucket: list[str] = []
    bucket_tokens = 0
    for s in sentences:
        st = count_tokens(s)
        if st > target:
            # Hard split by token slice — last resort
            enc = _get_encoder()
            if enc is None:
                char_budget = target * 3
                for i in range(0, len(s), char_budget):
                    yield s[i : i + char_budget]
                continue
            tokens = enc.encode(s)
            for i in range(0, len(tokens), target):
                yield enc.decode(tokens[i : i + target])
            continue
        if bucket_tokens + st > target and bucket:
            yield " ".join(bucket)
            bucket, bucket_tokens = [], 0
        bucket.append(s)
        bucket_tokens += st
    if bucket:
        yield " ".join(bucket)
