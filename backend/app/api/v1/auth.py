"""Authentication endpoints."""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Staff, Clinic
from app.schemas.auth import Token, UserResponse
from app.api.deps import CurrentUser

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Login to get access token."""
    # Find staff by email
    result = await db.execute(
        select(Staff).where(Staff.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not user.password_hash or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "clinic_id": str(user.clinic_id)}
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email or "",
        name=current_user.name,
        clinic_id=current_user.clinic_id,
        role=current_user.role,
    )


@router.post("/logout")
async def logout():
    """Logout (client should discard token)."""
    return {"message": "Logged out successfully"}


@router.post("/setup")
async def setup_initial_user(
    clinic_name: str,
    admin_name: str,
    admin_email: str,
    admin_phone: str,
    admin_password: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Set up initial clinic and admin user (for first-time setup only)."""
    # Check if any clinic exists
    result = await db.execute(select(Clinic).limit(1))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup already completed",
        )

    # Validate password
    if len(admin_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    # Create clinic
    clinic = Clinic(
        name=clinic_name,
        phone=admin_phone,
        escalation_contacts=[
            {
                "name": admin_name,
                "phone": admin_phone,
                "role": "admin",
                "priority": 1,
            }
        ],
    )
    db.add(clinic)
    await db.flush()

    # Create admin user with hashed password
    admin = Staff(
        clinic_id=clinic.id,
        name=admin_name,
        email=admin_email,
        phone=admin_phone,
        role="admin",
        password_hash=get_password_hash(admin_password),
    )
    db.add(admin)
    await db.commit()

    # Create access token
    access_token = create_access_token(
        data={"sub": str(admin.id), "clinic_id": str(clinic.id)}
    )

    return {
        "message": "Setup completed successfully",
        "access_token": access_token,
        "token_type": "bearer",
    }
