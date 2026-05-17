"""Pydantic schemas for chat sessions and messages."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FeedbackKind, MessageRole


class AskRequest(BaseModel):
    """Request body for the main consultation endpoint."""

    question: str = Field(..., min_length=2, max_length=2000)
    session_id: Optional[UUID] = None
    """If omitted, a new session is created automatically."""


class SourceInfo(BaseModel):
    """A citation surfaced to the user."""

    document_id: UUID
    chunk_id: UUID
    title: str
    short_title: Optional[str] = None
    doc_number: Optional[str] = None
    section_path: Optional[str] = None
    snippet: str
    score: float
    source_url: Optional[str] = None


class AnswerResponse(BaseModel):
    """Synchronous response returned by the /ask endpoint."""

    session_id: UUID
    message_id: UUID
    answer: str
    sources: list[SourceInfo]
    token_usage: dict = Field(default_factory=dict)
    retrieval_meta: dict = Field(default_factory=dict)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    sources: list = Field(default_factory=list)
    token_usage: dict = Field(default_factory=dict)
    retrieval_meta: dict = Field(default_factory=dict)
    created_at: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class SessionWithMessages(SessionOut):
    messages: list[MessageOut]


class SessionList(BaseModel):
    items: list[SessionOut]
    total: int


class FeedbackCreate(BaseModel):
    message_id: UUID
    kind: FeedbackKind
    comment: Optional[str] = Field(None, max_length=2000)


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    kind: FeedbackKind
    comment: Optional[str]
    created_at: datetime
