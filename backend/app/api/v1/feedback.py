"""Feedback endpoints — users rate assistant responses."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import ChatMessage, Feedback, MessageRole
from app.schemas import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate, user: CurrentUser, db: DbSession
) -> FeedbackOut:
    message = await db.scalar(select(ChatMessage).where(ChatMessage.id == payload.message_id))
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сообщение не найдено")
    if message.role != MessageRole.ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Оценивать можно только ответы ассистента",
        )

    fb = Feedback(
        user_id=user.id,
        message_id=payload.message_id,
        kind=payload.kind,
        comment=payload.comment,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return FeedbackOut.model_validate(fb)
