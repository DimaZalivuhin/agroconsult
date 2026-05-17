"""Chat session and message persistence."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ChatMessage, ChatSession, MessageRole, User


async def get_or_create_session(
    db: AsyncSession,
    user: User,
    session_id: UUID | None,
    *,
    first_question: str | None = None,
) -> ChatSession:
    """Fetch an existing session or create a new one for the user."""
    if session_id is not None:
        session = await db.scalar(
            select(ChatSession).where(
                ChatSession.id == session_id, ChatSession.user_id == user.id
            )
        )
        if session is not None:
            return session

    title = (first_question or "Новая консультация")[:120]
    session = ChatSession(user_id=user.id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def record_user_message(
    db: AsyncSession, session: ChatSession, content: str
) -> ChatMessage:
    msg = ChatMessage(
        session_id=session.id, role=MessageRole.USER, content=content
    )
    db.add(msg)
    session.message_count += 1
    await db.commit()
    await db.refresh(msg)
    return msg


async def record_assistant_message(
    db: AsyncSession,
    session: ChatSession,
    content: str,
    *,
    sources: list,
    token_usage: dict,
    retrieval_meta: dict,
) -> ChatMessage:
    msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=content,
        sources=sources,
        token_usage=token_usage,
        retrieval_meta=retrieval_meta,
    )
    db.add(msg)
    session.message_count += 1
    await db.commit()
    await db.refresh(msg)
    return msg


async def list_sessions(db: AsyncSession, user: User, *, limit: int = 50) -> tuple[list[ChatSession], int]:
    total = await db.scalar(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == user.id)
    )
    rows = await db.scalars(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
    )
    return list(rows), int(total or 0)


async def get_session_with_messages(
    db: AsyncSession, user: User, session_id: UUID
) -> ChatSession | None:
    return await db.scalar(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
    )


async def delete_session(db: AsyncSession, user: User, session_id: UUID) -> bool:
    session = await db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user.id
        )
    )
    if not session:
        return False
    await db.delete(session)
    await db.commit()
    return True
