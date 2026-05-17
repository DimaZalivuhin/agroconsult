"""Documents endpoints — listing for users, upload/admin for moderators."""
from datetime import date as dt_date
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import func, select

from app.api.deps import CurrentAdmin, CurrentUser, DbSession
from app.models import DocumentStatus, DocumentType, LegalDocument
from app.schemas import DocumentList, DocumentOut, DocumentUpdate
from app.services.ingest_service import delete_document, index_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentList)
async def list_documents(
    db: DbSession,
    _user: CurrentUser,
    doc_type: Optional[DocumentType] = Query(None),
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> DocumentList:
    stmt = select(LegalDocument)
    if doc_type is not None:
        stmt = stmt.where(LegalDocument.doc_type == doc_type)
    if status_filter is not None:
        stmt = stmt.where(LegalDocument.status == status_filter)
    if is_active is not None:
        stmt = stmt.where(LegalDocument.is_active == is_active)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await db.scalars(
        stmt.order_by(LegalDocument.created_at.desc()).limit(limit).offset(offset)
    )
    return DocumentList(
        items=[DocumentOut.model_validate(d) for d in rows],
        total=int(total or 0),
        limit=limit,
        offset=offset,
    )


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: UUID, db: DbSession, _user: CurrentUser) -> DocumentOut:
    doc = await db.scalar(select(LegalDocument).where(LegalDocument.id == document_id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")
    return DocumentOut.model_validate(doc)


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    db: DbSession,
    _admin: CurrentAdmin,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF / HTML / TXT файл нормативного акта"),
    title: str = Form(...),
    doc_type: DocumentType = Form(...),
    short_title: Optional[str] = Form(None),
    doc_number: Optional[str] = Form(None),
    doc_date: Optional[dt_date] = Form(None),
    effective_from: Optional[dt_date] = Form(None),
    issuing_body: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    tags: Optional[str] = Form(None, description="Comma-separated"),
    target_regions: Optional[str] = Form(None, description="Comma-separated region codes"),
    target_farm_types: Optional[str] = Form(None, description="Comma-separated"),
    target_directions: Optional[str] = Form(None, description="Comma-separated"),
    summary: Optional[str] = Form(None),
) -> DocumentOut:
    """Admin-only document upload. Indexing runs in a background task."""
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустой файл")

    def _split(s: Optional[str]) -> list[str]:
        return [x.strip() for x in (s or "").split(",") if x.strip()]

    doc = LegalDocument(
        title=title,
        short_title=short_title,
        doc_type=doc_type,
        doc_number=doc_number,
        doc_date=doc_date,
        effective_from=effective_from,
        issuing_body=issuing_body,
        source_url=source_url,
        tags=_split(tags),
        target_regions=_split(target_regions),
        target_farm_types=_split(target_farm_types),
        target_directions=_split(target_directions),
        summary=summary,
        status=DocumentStatus.PENDING,
        is_active=True,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(index_document, doc.id, raw, file.filename or "upload.bin")
    return DocumentOut.model_validate(doc)


@router.patch("/{document_id}", response_model=DocumentOut)
async def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    db: DbSession,
    _admin: CurrentAdmin,
) -> DocumentOut:
    doc = await db.scalar(select(LegalDocument).where(LegalDocument.id == document_id))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    await db.commit()
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(document_id: UUID, db: DbSession, _admin: CurrentAdmin) -> None:
    await delete_document(db, document_id)
