"""Pydantic schemas for API validation."""

from app.schemas.clinic import (
    ClinicCreate,
    ClinicResponse,
    ClinicUpdate,
    StaffCreate,
    StaffResponse,
    StaffUpdate,
    WorkingHours,
)
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    TimeSlot,
    AvailableSlotsResponse,
)
from app.schemas.conversation import (
    ConversationResponse,
    ConversationMessageResponse,
    ConversationState,
)
from app.schemas.common import PaginatedResponse, HealthResponse
from app.schemas.auth import Token, TokenData, UserLogin

__all__ = [
    "ClinicCreate",
    "ClinicResponse",
    "ClinicUpdate",
    "StaffCreate",
    "StaffResponse",
    "StaffUpdate",
    "WorkingHours",
    "AppointmentCreate",
    "AppointmentResponse",
    "AppointmentUpdate",
    "TimeSlot",
    "AvailableSlotsResponse",
    "ConversationResponse",
    "ConversationMessageResponse",
    "ConversationState",
    "PaginatedResponse",
    "HealthResponse",
    "Token",
    "TokenData",
    "UserLogin",
]
