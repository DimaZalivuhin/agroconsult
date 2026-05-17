"""Pydantic schemas for users and farmer profiles."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import FarmDirection, FarmerStatus, FarmType, UserRole


# ---------- Profile ----------
class FarmerProfileBase(BaseModel):
    region_code: Optional[str] = Field(None, max_length=8)
    region_name: Optional[str] = Field(None, max_length=128)
    farm_type: Optional[FarmType] = None
    direction: Optional[FarmDirection] = None
    status: Optional[FarmerStatus] = None
    okved: Optional[str] = Field(None, max_length=16)
    years_in_business: Optional[int] = Field(None, ge=0, le=100)
    inn: Optional[str] = Field(None, max_length=12)


class FarmerProfileCreate(FarmerProfileBase):
    pass


class FarmerProfileUpdate(FarmerProfileBase):
    pass


class FarmerProfileOut(FarmerProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


# ---------- User ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    profile: Optional[FarmerProfileOut] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
