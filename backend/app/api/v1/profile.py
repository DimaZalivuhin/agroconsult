"""Farmer profile endpoints."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import FarmerProfile
from app.schemas import FarmerProfileOut, FarmerProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=FarmerProfileOut)
async def get_my_profile(user: CurrentUser, db: DbSession) -> FarmerProfileOut:
    profile = await db.scalar(
        select(FarmerProfile).where(FarmerProfile.user_id == user.id)
    )
    if not profile:
        # Create on-demand for legacy accounts
        profile = FarmerProfile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return FarmerProfileOut.model_validate(profile)


@router.put("", response_model=FarmerProfileOut)
async def update_my_profile(
    payload: FarmerProfileUpdate, user: CurrentUser, db: DbSession
) -> FarmerProfileOut:
    profile = await db.scalar(
        select(FarmerProfile).where(FarmerProfile.user_id == user.id)
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не найден")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return FarmerProfileOut.model_validate(profile)
