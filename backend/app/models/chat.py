"""Chat sessions and messages."""
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin, UUIDMixin
from app.models.enums import MessageRole

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.user import User


class ChatSession(Base, UUIDMixin, TimestampMixin):
    """A continuous conversation between a farmer and the assistant."""

    __tablename__ = "chat_sessions"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(512), default="Новая консультация")
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base, UUIDMixin, TimestampMixin):
    """A single message in a chat session."""

    __tablename__ = "chat_messages"

    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Used citations and retrieval debug info for assistant messages
    sources: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    """Список словарей с источниками: [{document_id, chunk_id, title, snippet, score}, ...]."""

    retrieval_meta: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    """Метрики ретривера: latency, scores, n_candidates."""

    token_usage: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    """{prompt_tokens, completion_tokens, total_tokens}."""

    session: Mapped[ChatSession] = relationship(back_populates="messages")
    feedbacks: Mapped[list["Feedback"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
