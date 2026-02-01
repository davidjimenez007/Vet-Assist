"""Clinic and Staff database models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Clinic(Base):
    """Clinic model representing a veterinary clinic."""

    __tablename__ = "clinics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="America/Bogota")

    working_hours: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "monday": {"start": "08:00", "end": "18:00"},
            "tuesday": {"start": "08:00", "end": "18:00"},
            "wednesday": {"start": "08:00", "end": "18:00"},
            "thursday": {"start": "08:00", "end": "18:00"},
            "friday": {"start": "08:00", "end": "18:00"},
            "saturday": {"start": "09:00", "end": "14:00"},
            "sunday": None,
        },
    )

    appointment_duration_minutes: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "consultation": 30,
            "vaccination": 15,
            "surgery": 60,
            "grooming": 45,
            "emergency": 30,
        },
    )

    escalation_contacts: Mapped[dict] = mapped_column(JSONB, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    staff: Mapped[list["Staff"]] = relationship(
        "Staff", back_populates="clinic", cascade="all, delete-orphan"
    )
    clients: Mapped[list["Client"]] = relationship(
        "Client", back_populates="clinic", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="clinic", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="clinic", cascade="all, delete-orphan"
    )
    emergency_events: Mapped[list["EmergencyEvent"]] = relationship(
        "EmergencyEvent", back_populates="clinic", cascade="all, delete-orphan"
    )
    follow_up_protocols: Mapped[list["FollowUpProtocol"]] = relationship(
        "FollowUpProtocol", back_populates="clinic", cascade="all, delete-orphan"
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp", back_populates="clinic", cascade="all, delete-orphan"
    )


class Staff(Base):
    """Staff model representing veterinarians and assistants."""

    __tablename__ = "staff"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # veterinarian, assistant, admin
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_on_call: Mapped[bool] = mapped_column(Boolean, default=False)
    calendar_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="staff")
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="staff"
    )


# Import for type hints
from app.models.client import Client
from app.models.appointment import Appointment
from app.models.conversation import Conversation
from app.models.emergency import EmergencyEvent
from app.models.follow_up import FollowUpProtocol, FollowUp
