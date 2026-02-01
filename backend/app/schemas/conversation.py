"""Conversation schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ConversationMessageResponse(BaseModel):
    """Schema for conversation message response."""

    id: UUID
    role: str
    content: str
    audio_url: Optional[str] = None
    transcription_confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: UUID
    clinic_id: UUID
    client_id: Optional[UUID] = None
    channel: str
    external_id: Optional[str] = None
    intent: Optional[str] = None
    status: str
    outcome: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    metadata: dict

    # Nested data
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    message_count: int = 0

    class Config:
        from_attributes = True


class ConversationState(BaseModel):
    """Internal conversation state for agents."""

    id: UUID
    clinic_id: UUID
    channel: str
    current_state: str
    intent: Optional[str] = None
    collected_data: dict = {}
    messages: list[dict] = []


class ConversationSummary(BaseModel):
    """Summary view of a conversation."""

    id: UUID
    channel: str
    status: str
    outcome: Optional[str] = None
    started_at: datetime
    client_phone: Optional[str] = None
    summary: Optional[str] = None
