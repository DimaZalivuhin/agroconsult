"""User account and farmer profile models."""
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin, UUIDMixin
from app.models.enums import FarmDirection, FarmerStatus, FarmType, UserRole

if TYPE_CHECKING:
    from app.models.chat import ChatSession
    from app.models.feedback import Feedback


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]),
        default=UserRole.FARMER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    profile: Mapped["FarmerProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    feedbacks: Mapped[list["Feedback"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class FarmerProfile(Base, UUIDMixin, TimestampMixin):
    """Persistent characteristics of a farmer used to filter relevant measures."""

    __tablename__ = "farmer_profiles"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )

    region_code: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    """ОКАТО или код субъекта РФ (например '77' для Москвы)."""

    region_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    farm_type: Mapped[FarmType | None] = mapped_column(
        SAEnum(FarmType, name="farm_type", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    direction: Mapped[FarmDirection | None] = mapped_column(
        SAEnum(FarmDirection, name="farm_direction", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    status: Mapped[FarmerStatus | None] = mapped_column(
        SAEnum(FarmerStatus, name="farmer_status", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )

    okved: Mapped[str | None] = mapped_column(String(16), nullable=True)
    years_in_business: Mapped[int | None] = mapped_column(nullable=True)
    inn: Mapped[str | None] = mapped_column(String(12), nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")
