"""API dependencies for authentication and database sessions."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import Clinic, Staff, Client
from app.schemas.auth import TokenData
from app.schemas.client_auth import ClientTokenData

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Staff:
    """Get current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        token_data = TokenData(user_id=UUID(user_id), clinic_id=UUID(payload.get("clinic_id")))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await db.execute(select(Staff).where(Staff.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_clinic(
    current_user: Annotated[Staff, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Clinic:
    """Get current user's clinic."""
    result = await db.execute(select(Clinic).where(Clinic.id == current_user.clinic_id))
    clinic = result.scalar_one_or_none()

    if clinic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )

    return clinic


async def get_clinic_by_phone(
    phone: str,
    db: AsyncSession,
) -> Optional[Clinic]:
    """Get clinic by phone number (for webhook handling)."""
    result = await db.execute(select(Clinic).where(Clinic.phone == phone))
    return result.scalar_one_or_none()


async def get_current_client(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Client:
    """Get current authenticated client from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        # Check if this is a client token
        user_type = payload.get("user_type")
        if user_type != "client":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        client_id: str = payload.get("sub")
        clinic_id: str = payload.get("clinic_id")

        if client_id is None or clinic_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        token_data = ClientTokenData(
            client_id=UUID(client_id),
            clinic_id=UUID(clinic_id),
            user_type="client"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await db.execute(
        select(Client).where(
            Client.id == token_data.client_id,
            Client.clinic_id == token_data.clinic_id
        )
    )
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client not found",
        )

    return client


async def get_client_clinic(
    current_client: Annotated[Client, Depends(get_current_client)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Clinic:
    """Get current client's clinic."""
    result = await db.execute(select(Clinic).where(Clinic.id == current_client.clinic_id))
    clinic = result.scalar_one_or_none()

    if clinic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )

    return clinic


# Type aliases for dependency injection
CurrentUser = Annotated[Staff, Depends(get_current_user)]
CurrentClinic = Annotated[Clinic, Depends(get_current_clinic)]
CurrentClient = Annotated[Client, Depends(get_current_client)]
ClientClinic = Annotated[Clinic, Depends(get_client_clinic)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
