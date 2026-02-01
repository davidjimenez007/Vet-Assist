"""Appointment database model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Appointment(Base):
    """Appointment model representing scheduled veterinary appointments."""

    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True
    )
    pet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pets.id"), nullable=True
    )
    staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True
    )

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    appointment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="scheduled"
    )  # scheduled, confirmed, completed, cancelled, no_show

    priority: Mapped[str] = mapped_column(
        String(20), default="normal"
    )  # normal, high, emergency

    source: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # ai_voice, ai_whatsapp, manual, web
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    emergency_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Follow-up tracking
    follow_up_protocol: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # surgery, vaccination, consultation, etc.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="appointments")
    client: Mapped[Optional["Client"]] = relationship("Client", back_populates="appointments")
    pet: Mapped[Optional["Pet"]] = relationship("Pet", back_populates="appointments")
    staff: Mapped[Optional["Staff"]] = relationship("Staff", back_populates="appointments")
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp", back_populates="appointment", cascade="all, delete-orphan"
    )


# Import for type hints
from app.models.clinic import Clinic, Staff
from app.models.client import Client, Pet
from app.models.follow_up import FollowUp
