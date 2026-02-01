"""Emergency management API endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.api.deps import get_current_user
from app.models import Staff, EmergencyEvent, EmergencyAlert, Client, Conversation

router = APIRouter(prefix="/emergencies", tags=["emergencies"])


# ===========================================
# Schemas
# ===========================================

class EmergencyResponse(BaseModel):
    id: str
    client_phone: str
    pet_name: Optional[str]
    pet_species: Optional[str]
    description: Optional[str]
    keywords_detected: list[str]
    status: str
    priority: str
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime
    client_name: Optional[str] = None
    alerts_sent: int = 0

    class Config:
        from_attributes = True


class EmergencyListResponse(BaseModel):
    items: list[EmergencyResponse]
    total: int
    active_count: int


class AcknowledgeRequest(BaseModel):
    pass


class ResolveRequest(BaseModel):
    notes: Optional[str] = None
    was_false_alarm: bool = False


class EmergencyAlertResponse(BaseModel):
    id: str
    contact_phone: str
    contact_name: Optional[str]
    contact_role: Optional[str]
    status: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


# ===========================================
# Endpoints
# ===========================================

@router.get("", response_model=EmergencyListResponse)
async def list_emergencies(
    status: Optional[str] = Query(None, description="Filter by status: active, acknowledged, resolved"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """List all emergencies for the clinic."""
    query = (
        select(EmergencyEvent)
        .where(EmergencyEvent.clinic_id == current_user.clinic_id)
        .order_by(desc(EmergencyEvent.created_at))
    )

    if status:
        query = query.where(EmergencyEvent.status == status)

    # Get total count
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get active count
    active_query = select(func.count()).where(
        EmergencyEvent.clinic_id == current_user.clinic_id,
        EmergencyEvent.status == "active"
    )
    active_result = await db.execute(active_query)
    active_count = active_result.scalar() or 0

    # Get paginated results
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    emergencies = result.scalars().all()

    # Build response
    items = []
    for emergency in emergencies:
        # Get client name if available
        client_name = None
        if emergency.client_id:
            client = await db.get(Client, emergency.client_id)
            if client:
                client_name = client.name

        # Count alerts
        alerts_query = select(func.count()).where(
            EmergencyAlert.emergency_id == emergency.id
        )
        alerts_result = await db.execute(alerts_query)
        alerts_sent = alerts_result.scalar() or 0

        items.append(EmergencyResponse(
            id=str(emergency.id),
            client_phone=emergency.client_phone,
            pet_name=emergency.pet_name,
            pet_species=emergency.pet_species,
            description=emergency.description,
            keywords_detected=emergency.keywords_detected or [],
            status=emergency.status,
            priority=emergency.priority,
            acknowledged_at=emergency.acknowledged_at,
            resolved_at=emergency.resolved_at,
            resolution_notes=emergency.resolution_notes,
            created_at=emergency.created_at,
            client_name=client_name,
            alerts_sent=alerts_sent
        ))

    return EmergencyListResponse(
        items=items,
        total=total,
        active_count=active_count
    )


@router.get("/active", response_model=list[EmergencyResponse])
async def get_active_emergencies(
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Get all active emergencies (quick endpoint for dashboard)."""
    result = await db.execute(
        select(EmergencyEvent)
        .where(
            EmergencyEvent.clinic_id == current_user.clinic_id,
            EmergencyEvent.status == "active"
        )
        .order_by(desc(EmergencyEvent.created_at))
        .limit(10)
    )
    emergencies = result.scalars().all()

    items = []
    for emergency in emergencies:
        items.append(EmergencyResponse(
            id=str(emergency.id),
            client_phone=emergency.client_phone,
            pet_name=emergency.pet_name,
            pet_species=emergency.pet_species,
            description=emergency.description,
            keywords_detected=emergency.keywords_detected or [],
            status=emergency.status,
            priority=emergency.priority,
            acknowledged_at=emergency.acknowledged_at,
            resolved_at=emergency.resolved_at,
            resolution_notes=emergency.resolution_notes,
            created_at=emergency.created_at
        ))

    return items


@router.get("/{emergency_id}", response_model=EmergencyResponse)
async def get_emergency(
    emergency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Get a specific emergency by ID."""
    emergency = await db.get(EmergencyEvent, emergency_id)

    if not emergency or emergency.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Emergency not found")

    # Get client name
    client_name = None
    if emergency.client_id:
        client = await db.get(Client, emergency.client_id)
        if client:
            client_name = client.name

    # Count alerts
    alerts_query = select(func.count()).where(
        EmergencyAlert.emergency_id == emergency.id
    )
    alerts_result = await db.execute(alerts_query)
    alerts_sent = alerts_result.scalar() or 0

    return EmergencyResponse(
        id=str(emergency.id),
        client_phone=emergency.client_phone,
        pet_name=emergency.pet_name,
        pet_species=emergency.pet_species,
        description=emergency.description,
        keywords_detected=emergency.keywords_detected or [],
        status=emergency.status,
        priority=emergency.priority,
        acknowledged_at=emergency.acknowledged_at,
        resolved_at=emergency.resolved_at,
        resolution_notes=emergency.resolution_notes,
        created_at=emergency.created_at,
        client_name=client_name,
        alerts_sent=alerts_sent
    )


@router.get("/{emergency_id}/alerts", response_model=list[EmergencyAlertResponse])
async def get_emergency_alerts(
    emergency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Get all alerts sent for an emergency."""
    emergency = await db.get(EmergencyEvent, emergency_id)

    if not emergency or emergency.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Emergency not found")

    result = await db.execute(
        select(EmergencyAlert)
        .where(EmergencyAlert.emergency_id == emergency_id)
        .order_by(EmergencyAlert.created_at)
    )
    alerts = result.scalars().all()

    return [
        EmergencyAlertResponse(
            id=str(alert.id),
            contact_phone=alert.contact_phone,
            contact_name=alert.contact_name,
            contact_role=alert.contact_role,
            status=alert.status,
            sent_at=alert.sent_at,
            delivered_at=alert.delivered_at,
            error_message=alert.error_message
        )
        for alert in alerts
    ]


@router.post("/{emergency_id}/acknowledge")
async def acknowledge_emergency(
    emergency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Mark an emergency as acknowledged."""
    emergency = await db.get(EmergencyEvent, emergency_id)

    if not emergency or emergency.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Emergency not found")

    if emergency.status != "active":
        raise HTTPException(status_code=400, detail="Emergency is not active")

    emergency.status = "acknowledged"
    emergency.acknowledged_at = datetime.utcnow()
    emergency.acknowledged_by = current_user.id

    await db.commit()

    return {"message": "Emergency acknowledged", "status": "acknowledged"}


@router.post("/{emergency_id}/resolve")
async def resolve_emergency(
    emergency_id: uuid.UUID,
    request: ResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Mark an emergency as resolved."""
    emergency = await db.get(EmergencyEvent, emergency_id)

    if not emergency or emergency.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Emergency not found")

    if emergency.status == "resolved":
        raise HTTPException(status_code=400, detail="Emergency already resolved")

    # Update emergency
    if request.was_false_alarm:
        emergency.status = "false_alarm"
        # Increment client's false emergency count
        if emergency.client_id:
            client = await db.get(Client, emergency.client_id)
            if client:
                client.false_emergency_count += 1
                if client.false_emergency_count >= 2:
                    client.emergency_access_revoked = True
    else:
        emergency.status = "resolved"

    emergency.resolved_at = datetime.utcnow()
    emergency.resolved_by = current_user.id
    emergency.resolution_notes = request.notes

    await db.commit()

    return {
        "message": "Emergency resolved",
        "status": emergency.status,
        "was_false_alarm": request.was_false_alarm
    }


@router.get("/{emergency_id}/conversation")
async def get_emergency_conversation(
    emergency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Get the conversation associated with an emergency."""
    emergency = await db.get(EmergencyEvent, emergency_id)

    if not emergency or emergency.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Emergency not found")

    if not emergency.conversation_id:
        raise HTTPException(status_code=404, detail="No conversation associated")

    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == emergency.conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "conversation_id": str(conversation.id),
        "client_phone": conversation.client_phone,
        "state": conversation.state,
        "started_at": conversation.started_at,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at
            }
            for msg in sorted(conversation.messages, key=lambda m: m.created_at)
        ]
    }
