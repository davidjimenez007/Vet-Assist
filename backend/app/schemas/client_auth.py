"""Client authentication schemas for OTP-based login."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class OTPRequest(BaseModel):
    """Request OTP for client login."""

    phone: str
    clinic_id: UUID


class OTPRequestResponse(BaseModel):
    """Response after requesting OTP."""

    message: str
    expires_in_seconds: int = 300


class OTPVerify(BaseModel):
    """Verify OTP code."""

    phone: str
    clinic_id: UUID
    code: str


class ClientToken(BaseModel):
    """JWT token response for client."""

    access_token: str
    token_type: str = "bearer"


class ClientTokenData(BaseModel):
    """Token payload data for client."""

    client_id: Optional[UUID] = None
    clinic_id: Optional[UUID] = None
    user_type: str = "client"


class ClientInfo(BaseModel):
    """Client information response."""

    id: UUID
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    clinic_id: UUID
    clinic_name: str

    class Config:
        from_attributes = True


class PetInfo(BaseModel):
    """Pet information for client portal."""

    id: UUID
    name: Optional[str] = None
    species: str
    breed: Optional[str] = None

    class Config:
        from_attributes = True


class AppointmentInfo(BaseModel):
    """Appointment information for client portal."""

    id: UUID
    pet_name: Optional[str] = None
    pet_species: Optional[str] = None
    scheduled_at: str
    duration_minutes: int
    reason: Optional[str] = None
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ClinicInfo(BaseModel):
    """Basic clinic information for client portal."""

    id: UUID
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True


class PortalChatMessage(BaseModel):
    """Chat message for client portal."""

    message: str
    conversation_id: Optional[UUID] = None


class PortalChatResponse(BaseModel):
    """Chat response for client portal."""

    message: str
    conversation_id: UUID
    end_conversation: bool = False
    appointment_booked: bool = False
