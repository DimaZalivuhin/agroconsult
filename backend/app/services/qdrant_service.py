"""Wrapper around qdrant-client tuned to our metadata schema."""
from __future__ import annotations

import asyncio
from typing import Any, Optional
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("qdrant")


class QdrantService:
    """Vector store interactions for AgroConsult.

    Each point in the collection corresponds to one DocumentChunk in Postgres.
    The payload mirrors metadata necessary for filtered retrieval so we don't
    need to hit Postgres to filter.
    """

    def __init__(self) -> None:
        self.collection = settings.qdrant_collection
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            prefer_grpc=False,
            timeout=30,
        )

    async def close(self) -> None:
        await self.client.close()

    async def ensure_collection(self) -> None:
        """Idempotent — creates the collection on first launch."""
        collections = await self.client.get_collections()
        names = {c.name for c in collections.collections}
        if self.collection in names:
            return

        log.info(f"Creating Qdrant collection '{self.collection}'")
        await self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qm.VectorParams(
                size=settings.qdrant_vector_size,
                distance=qm.Distance.COSINE,
            ),
            optimizers_config=qm.OptimizersConfigDiff(default_segment_number=2),
        )
        # Useful indexed payload fields for fast filtering
        for field, schema in [
            ("document_id", qm.PayloadSchemaType.KEYWORD),
            ("doc_type", qm.PayloadSchemaType.KEYWORD),
            ("is_active", qm.PayloadSchemaType.BOOL),
            ("tags", qm.PayloadSchemaType.KEYWORD),
            ("target_regions", qm.PayloadSchemaType.KEYWORD),
            ("target_farm_types", qm.PayloadSchemaType.KEYWORD),
            ("target_directions", qm.PayloadSchemaType.KEYWORD),
        ]:
            try:
                await self.client.create_payload_index(
                    collection_name=self.collection,
                    field_name=field,
                    field_schema=schema,
                )
            except Exception as e:  # noqa: BLE001
                log.debug(f"Payload index for {field} already exists or skipped: {e}")

    async def upsert_chunks(
        self,
        chunk_ids: list[UUID],
        embeddings: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        """Upsert a batch of chunks into Qdrant."""
        assert len(chunk_ids) == len(embeddings) == len(payloads)
        points = [
            qm.PointStruct(id=str(chunk_id), vector=vector, payload=payload)
            for chunk_id, vector, payload in zip(chunk_ids, embeddings, payloads)
        ]
        await self.client.upsert(collection_name=self.collection, points=points, wait=True)

    async def delete_by_document(self, document_id: UUID) -> None:
        await self.client.delete(
            collection_name=self.collection,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="document_id",
                            match=qm.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
        )

    async def search(
        self,
        query_vector: list[float],
        *,
        top_k: int = 15,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Vector search with optional metadata filters.

        Filters accept lists for OR-within-field semantics and combine across
        fields with AND. Always restricts to is_active=True.
        """
        must: list[qm.Condition] = [
            qm.FieldCondition(key="is_active", match=qm.MatchValue(value=True))
        ]
        if filters:
            for field, value in filters.items():
                if value is None:
                    continue
                if isinstance(value, (list, tuple, set)):
                    values = list(value)
                    if not values:
                        continue
                    must.append(qm.FieldCondition(key=field, match=qm.MatchAny(any=values)))
                else:
                    must.append(qm.FieldCondition(key=field, match=qm.MatchValue(value=value)))

        qdrant_filter = qm.Filter(must=must) if must else None
        result = await self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            query_filter=qdrant_filter,
        )

        return [
            {
                "chunk_id": str(hit.id),
                "score": float(hit.score),
                "payload": dict(hit.payload or {}),
            }
            for hit in result
        ]


_qdrant: Optional[QdrantService] = None
_init_lock = asyncio.Lock()


async def get_qdrant() -> QdrantService:
    """Singleton accessor; ensures the collection exists on first call."""
    global _qdrant
    if _qdrant is not None:
        return _qdrant
    async with _init_lock:
        if _qdrant is None:
            svc = QdrantService()
            await svc.ensure_collection()
            _qdrant = svc
    return _qdrant
