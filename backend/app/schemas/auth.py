"""Authentication schemas."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""

    user_id: Optional[UUID] = None
    clinic_id: Optional[UUID] = None


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model."""

    id: UUID
    email: str
    name: str
    clinic_id: UUID
    role: str

    class Config:
        from_attributes = True
