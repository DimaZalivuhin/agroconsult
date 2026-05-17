"""Pydantic schemas for documents."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus, DocumentType


class DocumentCreate(BaseModel):
    """Metadata supplied by the admin when uploading a document."""

    title: str = Field(..., max_length=1024)
    short_title: Optional[str] = Field(None, max_length=512)
    doc_type: DocumentType
    doc_number: Optional[str] = Field(None, max_length=64)
    doc_date: Optional[date] = None
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    issuing_body: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=1024)
    tags: list[str] = Field(default_factory=list)
    target_regions: list[str] = Field(default_factory=list)
    target_farm_types: list[str] = Field(default_factory=list)
    target_directions: list[str] = Field(default_factory=list)
    summary: Optional[str] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    short_title: Optional[str] = None
    doc_type: Optional[DocumentType] = None
    is_active: Optional[bool] = None
    effective_until: Optional[date] = None
    tags: Optional[list[str]] = None
    target_regions: Optional[list[str]] = None
    target_farm_types: Optional[list[str]] = None
    target_directions: Optional[list[str]] = None
    summary: Optional[str] = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    short_title: Optional[str]
    doc_type: DocumentType
    doc_number: Optional[str]
    doc_date: Optional[date]
    effective_from: Optional[date]
    effective_until: Optional[date]
    issuing_body: Optional[str]
    source_url: Optional[str]
    tags: list[str]
    target_regions: list[str]
    target_farm_types: list[str]
    target_directions: list[str]
    status: DocumentStatus
    is_active: bool
    chunk_count: int
    error_message: Optional[str]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime


class DocumentList(BaseModel):
    items: list[DocumentOut]
    total: int
    limit: int
    offset: int


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    section_path: Optional[str]
    token_count: int
