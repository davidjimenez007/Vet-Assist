"""Conversation state management service."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models import Conversation, ConversationMessage, Client
from app.schemas.conversation import ConversationState


class ConversationService:
    """Service for managing conversation state and history."""

    # Conversation states
    STATE_GREETING = "greeting"
    STATE_INTENT_DETECTION = "intent_detection"
    STATE_SCHEDULE = "schedule"
    STATE_COLLECT_INFO = "collect_info"
    STATE_PROPOSE_SLOTS = "propose_slots"
    STATE_CONFIRM_BOOKING = "confirm_booking"
    STATE_EMERGENCY = "emergency"
    STATE_TRIAGE = "triage"
    STATE_ESCALATE = "escalate"
    STATE_QUESTION = "question"
    STATE_ANSWER = "answer"
    STATE_UNCLEAR = "unclear"
    STATE_CLARIFY = "clarify"
    STATE_END = "end"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self,
        clinic_id: UUID,
        channel: str,
        external_id: Optional[str] = None,
        client_phone: Optional[str] = None,
        client_id: Optional[UUID] = None,
    ) -> Conversation:
        """Create a new conversation."""
        # If client_id is not provided, try to find by phone
        if not client_id and client_phone:
            result = await self.db.execute(
                select(Client).where(
                    Client.clinic_id == clinic_id,
                    Client.phone == client_phone,
                )
            )
            client = result.scalar_one_or_none()
            if client:
                client_id = client.id

        conversation = Conversation(
            clinic_id=clinic_id,
            client_id=client_id,
            channel=channel,
            external_id=external_id,
            status="active",
            conversation_metadata={"current_state": self.STATE_GREETING, "collected_data": {}},
        )

        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID."""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_conversation_by_external_id(
        self, external_id: str
    ) -> Optional[Conversation]:
        """Get conversation by external ID (Twilio SID)."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.external_id == external_id)
            .order_by(desc(Conversation.started_at))
        )
        return result.scalar_one_or_none()

    async def get_active_conversation(
        self, clinic_id: UUID, client_phone: str, channel: str
    ) -> Optional[Conversation]:
        """Get active conversation for a client."""
        result = await self.db.execute(
            select(Conversation)
            .join(Client, Conversation.client_id == Client.id)
            .where(
                Conversation.clinic_id == clinic_id,
                Client.phone == client_phone,
                Conversation.channel == channel,
                Conversation.status == "active",
            )
            .order_by(desc(Conversation.started_at))
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        audio_url: Optional[str] = None,
        transcription_confidence: Optional[float] = None,
    ) -> ConversationMessage:
        """Add a message to the conversation."""
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            audio_url=audio_url,
            transcription_confidence=transcription_confidence,
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def get_messages(
        self, conversation_id: UUID, limit: int = 50
    ) -> list[ConversationMessage]:
        """Get messages for a conversation."""
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_state(
        self,
        conversation_id: UUID,
        new_state: str,
        collected_data: Optional[dict] = None,
        intent: Optional[str] = None,
    ) -> Conversation:
        """Update conversation state."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        metadata = conversation.conversation_metadata or {}
        metadata["current_state"] = new_state

        if collected_data:
            existing_data = metadata.get("collected_data", {})
            existing_data.update(collected_data)
            metadata["collected_data"] = existing_data

        conversation.conversation_metadata = metadata
        flag_modified(conversation, 'conversation_metadata')

        if intent:
            conversation.intent = intent

        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def end_conversation(
        self,
        conversation_id: UUID,
        outcome: str,
        status: str = "completed",
    ) -> Conversation:
        """End a conversation."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.status = status
        conversation.outcome = outcome
        conversation.ended_at = datetime.utcnow()

        metadata = conversation.conversation_metadata or {}
        metadata["current_state"] = self.STATE_END
        conversation.conversation_metadata = metadata

        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def get_conversation_state(self, conversation_id: UUID) -> ConversationState:
        """Get the current state of a conversation."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        messages = await self.get_messages(conversation_id)

        metadata = conversation.conversation_metadata or {}

        return ConversationState(
            id=conversation.id,
            clinic_id=conversation.clinic_id,
            channel=conversation.channel,
            current_state=metadata.get("current_state", self.STATE_GREETING),
            intent=conversation.intent,
            collected_data=metadata.get("collected_data", {}),
            messages=[
                {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
                for m in messages
            ],
        )

    async def get_recent_conversations(
        self,
        clinic_id: UUID,
        limit: int = 20,
        channel: Optional[str] = None,
    ) -> list[Conversation]:
        """Get recent conversations for a clinic."""
        query = select(Conversation).where(Conversation.clinic_id == clinic_id)

        if channel:
            query = query.where(Conversation.channel == channel)

        query = query.order_by(desc(Conversation.started_at)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def link_client(
        self, conversation_id: UUID, client_id: UUID
    ) -> Conversation:
        """Link a client to a conversation."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.client_id = client_id
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation
