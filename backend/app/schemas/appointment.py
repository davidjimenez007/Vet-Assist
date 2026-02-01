"""Appointment schemas."""

from datetime import date, datetime, time
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TimeSlot(BaseModel):
    """Available time slot."""

    start: str
    end: str


class AppointmentBase(BaseModel):
    """Base appointment schema."""

    appointment_type: str
    reason: Optional[str] = None


class AppointmentCreate(BaseModel):
    """Schema for creating an appointment."""

    client_phone: str
    client_name: Optional[str] = None
    pet_type: str = Field(..., description="Species: dog, cat, other")
    pet_name: Optional[str] = None
    reason: str
    start_time: datetime
    appointment_type: Optional[str] = None
    source: str = "manual"
    conversation_id: Optional[UUID] = None
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    appointment_type: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    staff_id: Optional[UUID] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Schema for appointment response."""

    id: UUID
    clinic_id: UUID
    client_id: Optional[UUID] = None
    pet_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    appointment_type: str
    reason: Optional[str] = None
    status: str
    source: str
    notes: Optional[str] = None
    created_at: datetime

    # Nested data
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    pet_name: Optional[str] = None
    pet_species: Optional[str] = None
    staff_name: Optional[str] = None

    class Config:
        from_attributes = True


class AvailableSlotsRequest(BaseModel):
    """Request for available slots."""

    date: date
    duration: int = 30
    staff_id: Optional[UUID] = None


class AvailableSlotsResponse(BaseModel):
    """Response with available time slots."""

    date: date
    available_slots: list[TimeSlot]
    next_available: Optional[dict] = None


class BookingResult(BaseModel):
    """Result of a booking attempt."""

    success: bool
    appointment: Optional[AppointmentResponse] = None
    error: Optional[str] = None
    alternative_slots: Optional[list[TimeSlot]] = None
    confirmation_message: Optional[str] = None
