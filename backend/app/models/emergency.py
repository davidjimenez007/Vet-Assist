"""Emergency event database models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmergencyEvent(Base):
    """Emergency event triggered from WhatsApp conversation."""

    __tablename__ = "emergency_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True
    )
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True
    )

    client_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    pet_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pet_species: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords_detected: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list
    )

    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, acknowledged, resolved, false_alarm
    priority: Mapped[str] = mapped_column(
        String(20), default="high"
    )  # high, critical

    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="emergency_events")
    conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation", back_populates="emergency_event"
    )
    client: Mapped[Optional["Client"]] = relationship("Client", back_populates="emergency_events")
    alerts: Mapped[list["EmergencyAlert"]] = relationship(
        "EmergencyAlert", back_populates="emergency", cascade="all, delete-orphan"
    )


class EmergencyAlert(Base):
    """Alert sent to staff for an emergency event."""

    __tablename__ = "emergency_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    emergency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emergency_events.id", ondelete="CASCADE"), nullable=False
    )

    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    message_content: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, sent, delivered, failed

    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    emergency: Mapped["EmergencyEvent"] = relationship(
        "EmergencyEvent", back_populates="alerts"
    )


# Import for type hints
from app.models.clinic import Clinic, Staff
from app.models.client import Client
from app.models.conversation import Conversation
