"""Auth endpoints: register, login, /me."""
from fastapi import APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from fastapi import Depends

from app.api.deps import CurrentUser, DbSession
from app.schemas import TokenResponse, UserCreate, UserOut
from app.services.auth_service import authenticate, issue_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DbSession) -> TokenResponse:
    user = await register_user(db, payload)
    token = issue_token(user)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    db: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """OAuth2 password flow — uses 'username' field for email."""
    user = await authenticate(db, form_data.username, form_data.password)
    token = issue_token(user)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
