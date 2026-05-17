"""User feedback on assistant answers."""
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin, UUIDMixin
from app.models.enums import FeedbackKind

if TYPE_CHECKING:
    from app.models.chat import ChatMessage
    from app.models.user import User


class Feedback(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "feedbacks"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    message_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("chat_messages.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[FeedbackKind] = mapped_column(
        SAEnum(FeedbackKind, name="feedback_kind", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="feedbacks")
    message: Mapped["ChatMessage"] = relationship(back_populates="feedbacks")
