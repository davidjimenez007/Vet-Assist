"""Client and Pet database models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Client(Base):
    """Client model representing pet owners."""

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="es")

    # Emergency abuse tracking
    false_emergency_count: Mapped[int] = mapped_column(Integer, default=0)
    emergency_access_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("clinic_id", "phone", name="uq_client_clinic_phone"),
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="clients")
    pets: Mapped[list["Pet"]] = relationship(
        "Pet", back_populates="client", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="client"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="client"
    )
    emergency_events: Mapped[list["EmergencyEvent"]] = relationship(
        "EmergencyEvent", back_populates="client"
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp", back_populates="client"
    )


class Pet(Base):
    """Pet model representing animals owned by clients."""

    __tablename__ = "pets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    species: Mapped[str] = mapped_column(String(50), nullable=False)  # dog, cat, other
    breed: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="pets")
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="pet"
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp", back_populates="pet"
    )


# Import for type hints
from app.models.clinic import Clinic
from app.models.appointment import Appointment
from app.models.conversation import Conversation
from app.models.emergency import EmergencyEvent
from app.models.follow_up import FollowUp
