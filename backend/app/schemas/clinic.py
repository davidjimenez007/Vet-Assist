"""Clinic and Staff schemas."""

from datetime import time
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class WorkingHours(BaseModel):
    """Working hours for a single day."""

    start: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class EscalationContact(BaseModel):
    """Emergency escalation contact."""

    name: str
    phone: str
    role: str
    priority: int = 1


class ClinicBase(BaseModel):
    """Base clinic schema."""

    name: str
    phone: str
    whatsapp_number: Optional[str] = None
    timezone: str = "America/Bogota"


class ClinicCreate(ClinicBase):
    """Schema for creating a clinic."""

    working_hours: Optional[dict[str, Optional[WorkingHours]]] = None
    appointment_duration_minutes: Optional[dict[str, int]] = None
    escalation_contacts: list[EscalationContact]


class ClinicUpdate(BaseModel):
    """Schema for updating a clinic."""

    name: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    timezone: Optional[str] = None
    working_hours: Optional[dict[str, Optional[WorkingHours]]] = None
    appointment_duration_minutes: Optional[dict[str, int]] = None
    escalation_contacts: Optional[list[EscalationContact]] = None
    settings: Optional[dict] = None


class ClinicResponse(ClinicBase):
    """Schema for clinic response."""

    id: UUID
    working_hours: dict
    appointment_duration_minutes: dict
    escalation_contacts: list
    settings: dict

    class Config:
        from_attributes = True


class StaffBase(BaseModel):
    """Base staff schema."""

    name: str
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_on_call: bool = False


class StaffCreate(StaffBase):
    """Schema for creating staff."""

    pass


class StaffUpdate(BaseModel):
    """Schema for updating staff."""

    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_on_call: Optional[bool] = None
    calendar_id: Optional[str] = None


class StaffResponse(StaffBase):
    """Schema for staff response."""

    id: UUID
    clinic_id: UUID
    calendar_id: Optional[str] = None

    class Config:
        from_attributes = True
