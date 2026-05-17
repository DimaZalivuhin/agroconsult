"""Knowledge-base documents and their chunks."""
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin, UUIDMixin
from app.models.enums import DocumentStatus, DocumentType

if TYPE_CHECKING:
    pass


class LegalDocument(Base, UUIDMixin, TimestampMixin):
    """A normative legal act stored in the knowledge base."""

    __tablename__ = "legal_documents"
    __table_args__ = (UniqueConstraint("doc_number", "doc_date", name="uq_doc_number_date"),)

    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    short_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    doc_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType, name="document_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    doc_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    """Например '1528', '264-ФЗ', 'приказ 25'."""

    doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    issuing_body: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """'Правительство РФ', 'Минсельхоз России' и т.д."""

    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Тематические маркеры для фильтрации
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")
    """Например ['agrostart', 'grant', 'beginner']."""

    target_regions: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")
    """Список кодов регионов; пусто — действует во всей РФ."""

    target_farm_types: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")
    target_directions: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")

    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, name="document_status", values_callable=lambda x: [e.value for e in x]),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    """False — если документ отменён."""

    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    """A retrievable text fragment of a legal document."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_index"),
    )

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("legal_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    # Структурная привязка (раздел/статья/пункт), если удалось распарсить
    section_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    """Например 'Раздел II / Статья 5 / пункт 3'."""

    # Полный набор метаданных, попадающий в Qdrant payload
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    document: Mapped[LegalDocument] = relationship(back_populates="chunks")
