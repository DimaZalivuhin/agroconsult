"""Auth service: registration, login, current-user resolution."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import FarmerProfile, User, UserRole
from app.schemas import UserCreate


async def register_user(db: AsyncSession, payload: UserCreate, role: UserRole = UserRole.FARMER) -> User:
    """Create a new user with empty profile."""
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже зарегистрирован",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=role,
        profile=FarmerProfile(),  # empty profile, user fills later
    )
    db.add(user)
    await db.commit()
    await db.refresh(user, attribute_names=["profile"])
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(
        select(User).where(User.email == email).options(selectinload(User.profile))
    )
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован",
        )
    return user


def issue_token(user: User) -> str:
    return create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "role": user.role.value},
    )


async def get_user_from_token(db: AsyncSession, token: str) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("missing sub")
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
        ) from e

    user = await db.scalar(
        select(User).where(User.id == UUID(user_id)).options(selectinload(User.profile))
    )
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или деактивирован",
        )
    return user
