"""Database engine, session factory and declarative base."""
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID, uuid4

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings

# Consistent naming convention so Alembic generates stable constraint names
_NAMING = {
    "ix": "ix_%(table_name)s_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base with shared metadata and mixin-friendly columns."""

    metadata = MetaData(naming_convention=_NAMING)


class UUIDMixin:
    """Mixin adding a UUID primary key."""

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )


class TimestampMixin:
    """Mixin adding created_at / updated_at columns managed by the database."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ----------------------------------------------------------------------
# Engine for Supabase Transaction Pooler (PgBouncer in transaction mode)
# ----------------------------------------------------------------------
# PgBouncer does NOT preserve session state across queries, so it does not
# support server-side prepared statements. We must:
#   1. Set `prepared_statement_cache_size=0` (SQLAlchemy-level cache off).
#   2. Set `statement_cache_size=0` on the asyncpg connection itself.
#   3. Use unique prepared-statement names per connection (uuid suffix) to
#      avoid name clashes when PgBouncer multiplexes physical connections.
#   4. Use NullPool — pgbouncer is the real pool, SQLAlchemy must not pool.
# Reference: https://magicstack.github.io/asyncpg/current/faq.html#why-am-i-getting-prepared-statement-errors
import uuid

from sqlalchemy.pool import NullPool


def _prepared_statement_name() -> str:
    return f"__as_{uuid.uuid4().hex}__"


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,
    prepared_statement_cache_size=0,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_name_func": _prepared_statement_name,
        "server_settings": {"jit": "off"},
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session and ensures cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
