"""Follow-up database models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FollowUpProtocol(Base):
    """Protocol template for follow-ups based on procedure type."""

    __tablename__ = "follow_up_protocols"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    procedure_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # surgery, vaccination, consultation, dental, etc.

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Schedule in hours after appointment
    schedule_hours: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), default=list
    )  # [24, 48, 72, 168]

    # Message templates (one per scheduled follow-up)
    message_templates: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list
    )

    # Keywords that trigger escalation
    escalation_keywords: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="follow_up_protocols")
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp", back_populates="protocol"
    )


class FollowUp(Base):
    """Scheduled follow-up message for a client."""

    __tablename__ = "follow_ups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    pet_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pets.id"), nullable=True
    )
    protocol_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("follow_up_protocols.id"), nullable=True
    )

    # Message to send
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    escalation_keywords: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list
    )

    # Scheduling
    sequence_number: Mapped[int] = mapped_column(Integer, default=1)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Execution
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, sent, responded, escalated, cancelled, failed

    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True
    )

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="follow_ups")
    appointment: Mapped["Appointment"] = relationship("Appointment", back_populates="follow_ups")
    client: Mapped["Client"] = relationship("Client", back_populates="follow_ups")
    pet: Mapped[Optional["Pet"]] = relationship("Pet", back_populates="follow_ups")
    protocol: Mapped[Optional["FollowUpProtocol"]] = relationship(
        "FollowUpProtocol", back_populates="follow_ups"
    )
    conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation", back_populates="follow_up"
    )
    responses: Mapped[list["FollowUpResponse"]] = relationship(
        "FollowUpResponse", back_populates="follow_up", cascade="all, delete-orphan"
    )


class FollowUpResponse(Base):
    """Client response to a follow-up message."""

    __tablename__ = "follow_up_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    follow_up_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("follow_ups.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True
    )

    response_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Analysis results
    analysis_result: Mapped[dict] = mapped_column(JSONB, default=dict)
    matched_keywords: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list
    )
    sentiment: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # positive, negative, neutral, concerning

    requires_escalation: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    escalation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    follow_up: Mapped["FollowUp"] = relationship("FollowUp", back_populates="responses")
    conversation: Mapped[Optional["Conversation"]] = relationship("Conversation")


# Import for type hints
from app.models.clinic import Clinic
from app.models.client import Client, Pet
from app.models.appointment import Appointment
from app.models.conversation import Conversation
