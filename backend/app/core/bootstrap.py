"""One-shot bootstrap helpers executed on application startup."""
from __future__ import annotations

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db import AsyncSessionLocal
from app.models import FarmerProfile, User, UserRole

log = get_logger("bootstrap")


async def ensure_admin_user() -> None:
    """Create the configured admin account on first run.

    Idempotent: does nothing when the account already exists.
    """
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == settings.admin_email))
        if existing:
            return
        admin = User(
            email=settings.admin_email,
            hashed_password=hash_password(settings.admin_password),
            full_name="Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            profile=FarmerProfile(),
        )
        db.add(admin)
        await db.commit()
        log.info(f"Admin user created: {settings.admin_email}")
