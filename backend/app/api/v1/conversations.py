"""Conversation endpoints."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import Conversation, ConversationMessage, Client
from app.schemas.conversation import ConversationResponse, ConversationMessageResponse
from app.api.deps import CurrentClinic, DBSession

router = APIRouter()


def conversation_to_response(conv: Conversation, message_count: int = 0) -> ConversationResponse:
    """Convert conversation model to response schema."""
    return ConversationResponse(
        id=conv.id,
        clinic_id=conv.clinic_id,
        client_id=conv.client_id,
        channel=conv.channel,
        external_id=conv.external_id,
        intent=conv.intent,
        status=conv.status,
        outcome=conv.outcome,
        started_at=conv.started_at,
        ended_at=conv.ended_at,
        metadata=conv.conversation_metadata or {},
        client_name=conv.client.name if conv.client else None,
        client_phone=conv.client.phone if conv.client else None,
        message_count=message_count,
    )


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_clinic: CurrentClinic,
    db: DBSession,
    channel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
):
    """List conversations with optional filters."""
    query = (
        select(Conversation)
        .where(Conversation.clinic_id == current_clinic.id)
        .options(selectinload(Conversation.client))
    )

    if channel:
        query = query.where(Conversation.channel == channel)

    if status:
        query = query.where(Conversation.status == status)

    if start_date:
        query = query.where(Conversation.started_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.where(Conversation.started_at <= datetime.combine(end_date, datetime.max.time()))

    query = query.order_by(Conversation.started_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    conversations = result.scalars().all()

    # Get message counts
    responses = []
    for conv in conversations:
        count_result = await db.execute(
            select(func.count(ConversationMessage.id))
            .where(ConversationMessage.conversation_id == conv.id)
        )
        message_count = count_result.scalar() or 0
        responses.append(conversation_to_response(conv, message_count))

    return responses


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Get a specific conversation."""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.clinic_id == current_clinic.id,
        )
        .options(selectinload(Conversation.client))
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    count_result = await db.execute(
        select(func.count(ConversationMessage.id))
        .where(ConversationMessage.conversation_id == conversation.id)
    )
    message_count = count_result.scalar() or 0

    return conversation_to_response(conversation, message_count)


@router.get("/{conversation_id}/messages", response_model=list[ConversationMessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Get messages for a conversation."""
    # Verify conversation belongs to clinic
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.clinic_id == current_clinic.id,
        )
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at)
    )
    messages = result.scalars().all()

    return [
        ConversationMessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            audio_url=msg.audio_url,
            transcription_confidence=msg.transcription_confidence,
            created_at=msg.created_at,
        )
        for msg in messages
    ]
