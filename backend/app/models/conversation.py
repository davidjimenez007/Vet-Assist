"""Conversation database models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conversation(Base):
    """Conversation model representing AI interaction sessions."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True
    )

    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # voice, whatsapp
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Twilio call/message SID
    client_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Conversation type
    conversation_type: Mapped[str] = mapped_column(
        String(20), default="inbound"
    )  # inbound, follow_up, outbound

    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="active"
    )  # active, completed, escalated, abandoned
    outcome: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # appointment_scheduled, question_answered, escalated, abandoned

    # State machine
    state: Mapped[str] = mapped_column(
        String(50), default="GREETING"
    )  # GREETING, INTENT_DETECTION, ASK_REASON, OFFER_SLOTS, etc.
    state_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_state_change: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timeout_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Extracted information
    extracted_pet_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extracted_pet_species: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extracted_client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extracted_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Emergency tracking
    emergency_keywords: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    emergency_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Offered slots for appointment flow
    offered_slots: Mapped[dict] = mapped_column(JSONB, default=dict)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    conversation_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    clinic: Mapped["Clinic"] = relationship("Clinic", back_populates="conversations")
    client: Mapped[Optional["Client"]] = relationship("Client", back_populates="conversations")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="conversation", cascade="all, delete-orphan"
    )
    emergency_event: Mapped[Optional["EmergencyEvent"]] = relationship(
        "EmergencyEvent", back_populates="conversation", uselist=False
    )
    follow_up: Mapped[Optional["FollowUp"]] = relationship(
        "FollowUp", back_populates="conversation", uselist=False
    )


class ConversationMessage(Base):
    """Individual message within a conversation."""

    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    audio_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcription_confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )


# Import for type hints
from app.models.clinic import Clinic
from app.models.client import Client
from app.models.emergency import EmergencyEvent
from app.models.follow_up import FollowUp
