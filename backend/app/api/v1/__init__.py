"""Versioned API router."""
from fastapi import APIRouter

from app.api.v1 import auth, chat, documents, feedback, profile

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(profile.router)
api_v1.include_router(documents.router)
api_v1.include_router(chat.router)
api_v1.include_router(feedback.router)
