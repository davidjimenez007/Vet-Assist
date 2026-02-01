"""Client authentication endpoints using OTP."""

import logging
import random
import string
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Client, Clinic
from app.models.client_otp import ClientOTP
from app.schemas.client_auth import (
    ClientInfo,
    ClientToken,
    OTPRequest,
    OTPRequestResponse,
    OTPVerify,
)
from app.api.deps import CurrentClient, ClientClinic
from app.services.twilio_client import TwilioService

logger = logging.getLogger(__name__)

router = APIRouter()

OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3
OTP_RATE_LIMIT_SECONDS = 60


def generate_otp_code() -> str:
    """Generate a 6-digit OTP code."""
    return "".join(random.choices(string.digits, k=6))


def create_client_access_token(client_id: str, clinic_id: str, expires_delta: timedelta = None) -> str:
    """Create a JWT access token for client."""
    to_encode = {
        "sub": client_id,
        "clinic_id": clinic_id,
        "user_type": "client",
    }

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


@router.post("/otp/request", response_model=OTPRequestResponse)
async def request_otp(
    data: OTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Request OTP code for client login."""
    # Verify clinic exists
    result = await db.execute(select(Clinic).where(Clinic.id == data.clinic_id))
    clinic = result.scalar_one_or_none()

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found",
        )

    # Check rate limit - only allow one OTP request per minute
    now = datetime.utcnow()
    rate_limit_time = now - timedelta(seconds=OTP_RATE_LIMIT_SECONDS)

    result = await db.execute(
        select(ClientOTP).where(
            ClientOTP.phone == data.phone,
            ClientOTP.clinic_id == data.clinic_id,
            ClientOTP.created_at > rate_limit_time,
        )
    )
    recent_otp = result.scalar_one_or_none()

    if recent_otp:
        seconds_remaining = OTP_RATE_LIMIT_SECONDS - int((now - recent_otp.created_at.replace(tzinfo=None)).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {seconds_remaining} seconds before requesting a new code",
        )

    # Delete any existing OTP for this phone/clinic
    await db.execute(
        delete(ClientOTP).where(
            ClientOTP.phone == data.phone,
            ClientOTP.clinic_id == data.clinic_id,
        )
    )

    # Generate new OTP
    code = generate_otp_code()
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp = ClientOTP(
        phone=data.phone,
        clinic_id=data.clinic_id,
        code=code,
        expires_at=expires_at,
    )
    db.add(otp)
    await db.commit()

    # Send OTP via SMS
    twilio = TwilioService()
    message = f"Tu codigo de acceso a {clinic.name} es: {code}. Expira en {OTP_EXPIRY_MINUTES} minutos."

    sms_sent = await twilio.send_sms(data.phone, message)
    if not sms_sent:
        logger.warning(f"Failed to send SMS to {data.phone}")

    # For development, log the code
    logger.info(f"[OTP] Phone: {data.phone}, Code: {code}")

    return OTPRequestResponse(
        message="Codigo enviado por SMS",
        expires_in_seconds=OTP_EXPIRY_MINUTES * 60,
    )


@router.post("/otp/verify", response_model=ClientToken)
async def verify_otp(
    data: OTPVerify,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify OTP code and return access token."""
    now = datetime.utcnow()

    # Find the OTP record
    result = await db.execute(
        select(ClientOTP).where(
            ClientOTP.phone == data.phone,
            ClientOTP.clinic_id == data.clinic_id,
            ClientOTP.verified == False,
        )
    )
    otp = result.scalar_one_or_none()

    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending verification found. Please request a new code.",
        )

    # Check expiration
    if otp.expires_at.replace(tzinfo=None) < now:
        await db.delete(otp)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code expired. Please request a new one.",
        )

    # Check attempts
    if otp.attempts >= MAX_OTP_ATTEMPTS:
        await db.delete(otp)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many attempts. Please request a new code.",
        )

    # Verify code
    if otp.code != data.code:
        otp.attempts += 1
        await db.commit()
        attempts_left = MAX_OTP_ATTEMPTS - otp.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid code. {attempts_left} attempts remaining.",
        )

    # Mark as verified
    otp.verified = True
    await db.commit()

    # Find or create client
    result = await db.execute(
        select(Client).where(
            Client.phone == data.phone,
            Client.clinic_id == data.clinic_id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        # Create new client
        client = Client(
            phone=data.phone,
            clinic_id=data.clinic_id,
        )
        db.add(client)
        await db.commit()
        await db.refresh(client)

    # Clean up OTP record
    await db.delete(otp)
    await db.commit()

    # Generate access token
    access_token = create_client_access_token(
        client_id=str(client.id),
        clinic_id=str(client.clinic_id),
    )

    return ClientToken(access_token=access_token)


@router.get("/me", response_model=ClientInfo)
async def get_current_client_info(
    current_client: CurrentClient,
    current_clinic: ClientClinic,
):
    """Get current client information."""
    return ClientInfo(
        id=current_client.id,
        phone=current_client.phone,
        name=current_client.name,
        email=current_client.email,
        clinic_id=current_client.clinic_id,
        clinic_name=current_clinic.name,
    )
