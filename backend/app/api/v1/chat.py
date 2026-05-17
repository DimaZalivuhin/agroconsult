"""Chat endpoints — main /ask and session history."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.rag.orchestrator import answer_question
from app.schemas import (
    AnswerResponse,
    AskRequest,
    MessageOut,
    SessionList,
    SessionOut,
    SessionWithMessages,
    SourceInfo,
)
from app.schemas.user import FarmerProfileOut
from app.services.chat_service import (
    delete_session,
    get_or_create_session,
    get_session_with_messages,
    list_sessions,
    record_assistant_message,
    record_user_message,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _profile_dict(profile) -> dict | None:
    if profile is None:
        return None
    p = FarmerProfileOut.model_validate(profile).model_dump()
    return {
        "region_code": p.get("region_code"),
        "region_name": p.get("region_name"),
        "farm_type": p["farm_type"].value if p.get("farm_type") else None,
        "direction": p["direction"].value if p.get("direction") else None,
        "status": p["status"].value if p.get("status") else None,
        "years_in_business": p.get("years_in_business"),
    }


@router.post("/ask", response_model=AnswerResponse)
async def ask(payload: AskRequest, user: CurrentUser, db: DbSession) -> AnswerResponse:
    """Main consultation endpoint — synchronous (non-streaming) for MVP."""
    session = await get_or_create_session(
        db, user, payload.session_id, first_question=payload.question
    )
    await record_user_message(db, session, payload.question)

    profile_dict = _profile_dict(user.profile)
    result = await answer_question(payload.question, profile=profile_dict)

    msg = await record_assistant_message(
        db,
        session,
        result.answer,
        sources=result.sources,
        token_usage=result.token_usage,
        retrieval_meta=result.retrieval_meta,
    )

    return AnswerResponse(
        session_id=session.id,
        message_id=msg.id,
        answer=result.answer,
        sources=[SourceInfo(**src) for src in result.sources],
        token_usage=result.token_usage,
        retrieval_meta=result.retrieval_meta,
    )


@router.get("/sessions", response_model=SessionList)
async def my_sessions(user: CurrentUser, db: DbSession) -> SessionList:
    items, total = await list_sessions(db, user)
    return SessionList(
        items=[SessionOut.model_validate(s) for s in items], total=total
    )


@router.get("/sessions/{session_id}", response_model=SessionWithMessages)
async def session_detail(
    session_id: UUID, user: CurrentUser, db: DbSession
) -> SessionWithMessages:
    session = await get_session_with_messages(db, user, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена")
    return SessionWithMessages(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        message_count=session.message_count,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[MessageOut.model_validate(m) for m in session.messages],
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_session(session_id: UUID, user: CurrentUser, db: DbSession) -> None:
    ok = await delete_session(db, user, session_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена")
