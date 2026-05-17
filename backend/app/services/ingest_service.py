"""Document ingestion service: parse → chunk → embed → upsert."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db import AsyncSessionLocal
from app.models import DocumentChunk, DocumentStatus, LegalDocument
from app.rag.chunker import chunk_text
from app.rag.parser import parse_bytes, parse_file
from app.services.gigachat import get_gigachat
from app.services.qdrant_service import get_qdrant

log = get_logger("ingest")


async def _set_status(
    db: AsyncSession,
    doc: LegalDocument,
    status: DocumentStatus,
    error: str | None = None,
) -> None:
    doc.status = status
    doc.error_message = error
    await db.commit()


def _build_payload(doc: LegalDocument, chunk: DocumentChunk) -> dict[str, Any]:
    """Build the Qdrant payload mirroring metadata used for retrieval/UI."""
    return {
        "document_id": str(doc.id),
        "chunk_index": chunk.chunk_index,
        "title": doc.title,
        "short_title": doc.short_title,
        "doc_type": doc.doc_type.value,
        "doc_number": doc.doc_number,
        "doc_date": doc.doc_date.isoformat() if doc.doc_date else None,
        "issuing_body": doc.issuing_body,
        "section_path": chunk.section_path,
        "content": chunk.content,
        "tags": list(doc.tags or []),
        "target_regions": list(doc.target_regions or []),
        "target_farm_types": list(doc.target_farm_types or []),
        "target_directions": list(doc.target_directions or []),
        "is_active": doc.is_active,
        "source_url": doc.source_url,
    }


async def index_document(document_id: UUID, raw_bytes: bytes, filename: str) -> None:
    """Background task: parse, chunk, embed and upsert into vector store.

    Runs in a fresh DB session (do not pass one in).
    """
    async with AsyncSessionLocal() as db:
        doc = await db.scalar(select(LegalDocument).where(LegalDocument.id == document_id))
        if not doc:
            log.error(f"Document {document_id} not found during indexing")
            return

        try:
            await _set_status(db, doc, DocumentStatus.PARSING)
            text = parse_bytes(raw_bytes, filename)
            if not text:
                raise ValueError("Parser returned empty text")

            await _set_status(db, doc, DocumentStatus.CHUNKING)
            chunks = chunk_text(text)
            if not chunks:
                raise ValueError("Chunker produced no chunks")

            log.info(f"Document {doc.id}: {len(chunks)} chunks produced")

            # Persist chunks in DB
            await db.execute(
                # Clear any previous chunks (re-indexing case)
                DocumentChunk.__table__.delete().where(DocumentChunk.document_id == doc.id)
            )
            db_chunks: list[DocumentChunk] = []
            for c in chunks:
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c.index,
                    content=c.content,
                    token_count=c.token_count,
                    section_path=c.section_path,
                )
                db.add(db_chunk)
                db_chunks.append(db_chunk)
            await db.commit()
            for chunk in db_chunks:
                await db.refresh(chunk)

            await _set_status(db, doc, DocumentStatus.EMBEDDING)
            giga = get_gigachat()
            qdrant = await get_qdrant()

            # GigaChat /embeddings has a hard limit on total tokens per request.
            # With rag_chunk_size=900 tokens, even 8 chunks can exceed it on
            # docs with long paragraphs. We start with a conservative batch
            # of 4 and auto-halve on 413 Payload Too Large.
            BATCH = 4
            i = 0
            while i < len(db_chunks):
                current_batch = BATCH
                while True:
                    batch = db_chunks[i : i + current_batch]
                    texts = [c.content for c in batch]
                    try:
                        vectors = await giga.embed(texts)
                        break  # success — leave the retry loop
                    except Exception as e:  # noqa: BLE001
                        # 413 from GigaChat: payload too large. Halve and retry.
                        msg = str(e)
                        if "413" in msg and current_batch > 1:
                            current_batch = max(1, current_batch // 2)
                            log.warning(
                                f"Document {doc.id}: 413 from GigaChat, "
                                f"retrying with batch={current_batch}"
                            )
                            continue
                        raise  # other errors → fail the document
                payloads = [_build_payload(doc, c) for c in batch]
                await qdrant.upsert_chunks(
                    chunk_ids=[c.id for c in batch],
                    embeddings=vectors,
                    payloads=payloads,
                )
                log.info(
                    f"Document {doc.id}: indexed "
                    f"{min(i + current_batch, len(db_chunks))}/{len(db_chunks)}"
                )
                i += current_batch

            doc.chunk_count = len(db_chunks)
            await _set_status(db, doc, DocumentStatus.INDEXED)
            log.info(f"Document {doc.id} indexed successfully")
        except Exception as e:  # noqa: BLE001
            log.exception(f"Indexing failed for {document_id}: {e}")
            await _set_status(db, doc, DocumentStatus.FAILED, error=str(e)[:500])


async def reindex_from_file(document_id: UUID, file_path: str) -> None:
    """Helper used by CLI seed script when file is already on disk."""
    text_bytes = open(file_path, "rb").read()
    filename = file_path.rsplit("/", 1)[-1]
    await index_document(document_id, text_bytes, filename)


async def delete_document(db: AsyncSession, document_id: UUID) -> None:
    """Hard-delete document and purge its vectors."""
    doc = await db.scalar(select(LegalDocument).where(LegalDocument.id == document_id))
    if not doc:
        return
    qdrant = await get_qdrant()
    try:
        await qdrant.delete_by_document(document_id)
    except Exception as e:  # noqa: BLE001
        log.warning(f"Failed to purge vectors for {document_id}: {e}")
    await db.delete(doc)
    await db.commit()


async def parse_local_file_for_seed(file_path: str) -> str:
    """Used by the seed CLI script — returns plain text from a local file."""
    return parse_file(file_path)
