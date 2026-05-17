"""Chunker unit tests — fast, no external dependencies (tiktoken is lazy)."""
from app.rag.chunker import chunk_text


def test_chunker_returns_chunks_for_normal_text():
    text = "\n\n".join(["Параграф номер один." * 5 for _ in range(20)])
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(c.token_count > 0 for c in chunks)
    assert all(c.content for c in chunks)


def test_chunker_preserves_short_text_in_single_chunk():
    text = "Один короткий параграф."
    chunks = chunk_text(text, chunk_size=200, overlap=20)
    assert len(chunks) == 1
    assert chunks[0].content == text


def test_chunker_indexes_are_sequential():
    text = "\n\n".join([f"Параграф {i} " + ("слово " * 30) for i in range(30)])
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    indices = [c.index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunker_handles_empty_input():
    assert chunk_text("", chunk_size=100, overlap=20) == []
    assert chunk_text("   \n\n  \n", chunk_size=100, overlap=20) == []
