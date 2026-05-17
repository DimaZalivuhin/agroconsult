"""Database engine, session factory and declarative base.

Supabase Transaction Pooler (port 6543) runs PgBouncer in transaction mode.
PgBouncer doesn't preserve session state, so asyncpg's prepared statements
collide between requests. Fix:

  1. Use NullPool — let PgBouncer do the pooling.
  2. statement_cache_size=0 in asyncpg connect_args.
  3. Pass a per-connection unique prepared_statement_name_func to asyncpg
     via the `creator` hook so names never clash across multiplexed conns.
"""
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
from sqlalchemy.pool import NullPool

from app.core.config import settings

_NAMING = {
    "ix": "ix_%(table_name)s_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=_NAMING)


class UU
