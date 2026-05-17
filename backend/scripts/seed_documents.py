"""Seed the knowledge base from a YAML manifest + a folder of raw documents.

Usage:
    python -m scripts.seed_documents \
        --manifest scripts/documents_manifest.yaml \
        --corpus-dir ../data/corpus_raw \
        [--skip-existing]

The script expects each entry in the manifest to map to a real file in
``corpus_dir``. Files can be plain text (.txt), HTML (.html) or PDF (.pdf).
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path

import yaml
from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.db import AsyncSessionLocal
from app.models import DocumentStatus, DocumentType, LegalDocument
from app.services.ingest_service import index_document

configure_logging()
log = get_logger("seed")


def _parse_date(value):
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


async def _process_entry(entry: dict, corpus_dir: Path, skip_existing: bool) -> None:
    filename = entry["filename"]
    path = corpus_dir / filename
    if not path.exists():
        log.warning(f"File missing for entry: {filename} — skipping")
        return

    async with AsyncSessionLocal() as db:
        existing = await db.scalar(
            select(LegalDocument).where(LegalDocument.title == entry["title"])
        )

    if existing and skip_existing:
        if existing.status == DocumentStatus.INDEXED:
            log.info(f"Skip already indexed: {entry['short_title']}")
            return

    raw = path.read_bytes()

    if existing:
        document_id = existing.id
        log.info(f"Re-indexing existing document: {entry['short_title']}")
    else:
        async with AsyncSessionLocal() as db:
            doc = LegalDocument(
                title=entry["title"],
                short_title=entry.get("short_title"),
                doc_type=DocumentType(entry["doc_type"]),
                doc_number=entry.get("doc_number"),
                doc_date=_parse_date(entry.get("doc_date")),
                effective_from=_parse_date(entry.get("effective_from")),
                issuing_body=entry.get("issuing_body"),
                source_url=entry.get("source_url"),
                tags=entry.get("tags", []) or [],
                target_regions=entry.get("target_regions", []) or [],
                target_farm_types=entry.get("target_farm_types", []) or [],
                target_directions=entry.get("target_directions", []) or [],
                summary=entry.get("summary"),
                status=DocumentStatus.PENDING,
                is_active=True,
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)
            document_id = doc.id
            log.info(f"Created document: {entry['short_title']} ({document_id})")

    await index_document(document_id, raw, filename)


async def main(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    corpus_dir = Path(args.corpus_dir)
    if not manifest_path.exists():
        log.error(f"Manifest not found: {manifest_path}")
        sys.exit(1)
    if not corpus_dir.exists():
        log.error(f"Corpus dir not found: {corpus_dir}")
        sys.exit(1)

    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    entries = data.get("documents") or []
    log.info(f"Manifest contains {len(entries)} document entries")

    for entry in entries:
        try:
            await _process_entry(entry, corpus_dir, args.skip_existing)
        except Exception as e:  # noqa: BLE001
            log.exception(f"Failed to process {entry.get('filename')}: {e}")

    log.info("Seeding complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed AgroConsult knowledge base")
    parser.add_argument(
        "--manifest",
        default="scripts/documents_manifest.yaml",
        help="Path to the YAML manifest",
    )
    parser.add_argument(
        "--corpus-dir",
        default="../data/corpus_raw",
        help="Directory with raw document files referenced by the manifest",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Do not re-index documents that already exist and are marked INDEXED",
    )
    args = parser.parse_args()
    asyncio.run(main(args))
