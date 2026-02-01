"""Follow-up management API endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models import (
    Staff, FollowUp, FollowUpProtocol, FollowUpResponse,
    Appointment, Client, Pet
)

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


# ===========================================
# Schemas
# ===========================================

class FollowUpResponse_(BaseModel):
    id: str
    appointment_id: str
    client_id: str
    pet_id: Optional[str]
    message_template: str
    sequence_number: int
    scheduled_at: datetime
    status: str
    sent_at: Optional[datetime]
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    pet_name: Optional[str] = None
    appointment_reason: Optional[str] = None

    class Config:
        from_attributes = True


class FollowUpListResponse(BaseModel):
    items: list[FollowUpResponse_]
    total: int
    pending_count: int


class ProtocolResponse(BaseModel):
    id: str
    name: str
    procedure_type: str
    is_active: bool
    schedule_hours: list[int]
    message_templates: list[str]
    escalation_keywords: list[str]

    class Config:
        from_attributes = True


class CreateProtocolRequest(BaseModel):
    name: str
    procedure_type: str
    schedule_hours: list[int]
    message_templates: list[str]
    escalation_keywords: list[str] = []


class UpdateProtocolRequest(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    schedule_hours: Optional[list[int]] = None
    message_templates: Optional[list[str]] = None
    escalation_keywords: Optional[list[str]] = None


class ScheduleFollowUpsRequest(BaseModel):
    appointment_id: str
    protocol_id: Optional[str] = None
    procedure_type: Optional[str] = None


# ===========================================
# Follow-up Endpoints
# ===========================================

@router.get("", response_model=FollowUpListResponse)
async def list_follow_ups(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """List all follow-ups for the clinic."""
    query = (
        select(FollowUp)
        .where(FollowUp.clinic_id == current_user.clinic_id)
        .order_by(FollowUp.scheduled_at)
    )

    if status:
        query = query.where(FollowUp.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get pending count
    pending_query = select(func.count()).where(
        FollowUp.clinic_id == current_user.clinic_id,
        FollowUp.status == "pending"
    )
    pending_result = await db.execute(pending_query)
    pending_count = pending_result.scalar() or 0

    # Get paginated results
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    follow_ups = result.scalars().all()

    # Build response with related data
    items = []
    for fu in follow_ups:
        client = await db.get(Client, fu.client_id) if fu.client_id else None
        pet = await db.get(Pet, fu.pet_id) if fu.pet_id else None
        appointment = await db.get(Appointment, fu.appointment_id)

        items.append(FollowUpResponse_(
            id=str(fu.id),
            appointment_id=str(fu.appointment_id),
            client_id=str(fu.client_id),
            pet_id=str(fu.pet_id) if fu.pet_id else None,
            message_template=fu.message_template,
            sequence_number=fu.sequence_number,
            scheduled_at=fu.scheduled_at,
            status=fu.status,
            sent_at=fu.sent_at,
            client_name=client.name if client else None,
            client_phone=client.phone if client else None,
            pet_name=pet.name if pet else None,
            appointment_reason=appointment.reason if appointment else None
        ))

    return FollowUpListResponse(
        items=items,
        total=total,
        pending_count=pending_count
    )


@router.get("/pending", response_model=list[FollowUpResponse_])
async def get_pending_follow_ups(
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Get pending follow-ups due in the next 24 hours."""
    now = datetime.utcnow()
    tomorrow = now + timedelta(hours=24)

    result = await db.execute(
        select(FollowUp)
        .where(
            FollowUp.clinic_id == current_user.clinic_id,
            FollowUp.status == "pending",
            FollowUp.scheduled_at <= tomorrow
        )
        .order_by(FollowUp.scheduled_at)
        .limit(20)
    )
    follow_ups = result.scalars().all()

    items = []
    for fu in follow_ups:
        client = await db.get(Client, fu.client_id) if fu.client_id else None
        pet = await db.get(Pet, fu.pet_id) if fu.pet_id else None

        items.append(FollowUpResponse_(
            id=str(fu.id),
            appointment_id=str(fu.appointment_id),
            client_id=str(fu.client_id),
            pet_id=str(fu.pet_id) if fu.pet_id else None,
            message_template=fu.message_template,
            sequence_number=fu.sequence_number,
            scheduled_at=fu.scheduled_at,
            status=fu.status,
            sent_at=fu.sent_at,
            client_name=client.name if client else None,
            client_phone=client.phone if client else None,
            pet_name=pet.name if pet else None
        ))

    return items


@router.post("/schedule")
async def schedule_follow_ups(
    request: ScheduleFollowUpsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Schedule follow-ups for a completed appointment."""
    appointment = await db.get(Appointment, uuid.UUID(request.appointment_id))

    if not appointment or appointment.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Get protocol
    protocol = None
    if request.protocol_id:
        protocol = await db.get(FollowUpProtocol, uuid.UUID(request.protocol_id))
    elif request.procedure_type:
        result = await db.execute(
            select(FollowUpProtocol)
            .where(
                FollowUpProtocol.clinic_id == current_user.clinic_id,
                FollowUpProtocol.procedure_type == request.procedure_type,
                FollowUpProtocol.is_active == True
            )
            .limit(1)
        )
        protocol = result.scalar_one_or_none()

    if not protocol:
        # Use default protocol
        schedule_hours = [24, 48]
        message_templates = [
            "Hola, ¿cómo sigue {pet_name} después de la consulta de ayer?",
            "Hola, seguimiento del día 2. ¿Cómo va {pet_name}? ¿Alguna novedad?"
        ]
        escalation_keywords = ["mal", "peor", "sangre", "fiebre", "no come"]
    else:
        schedule_hours = protocol.schedule_hours
        message_templates = protocol.message_templates
        escalation_keywords = protocol.escalation_keywords

    # Get pet name for templates
    pet_name = "tu mascota"
    if appointment.pet_id:
        pet = await db.get(Pet, appointment.pet_id)
        if pet and pet.name:
            pet_name = pet.name

    # Create follow-ups
    base_time = appointment.end_time or appointment.start_time
    created = []

    for i, hours in enumerate(schedule_hours):
        if i >= len(message_templates):
            break

        template = message_templates[i].replace("{pet_name}", pet_name)

        follow_up = FollowUp(
            clinic_id=current_user.clinic_id,
            appointment_id=appointment.id,
            client_id=appointment.client_id,
            pet_id=appointment.pet_id,
            protocol_id=protocol.id if protocol else None,
            message_template=template,
            escalation_keywords=escalation_keywords,
            sequence_number=i + 1,
            scheduled_at=base_time + timedelta(hours=hours),
            status="pending"
        )
        db.add(follow_up)
        created.append(follow_up)

    await db.commit()

    return {
        "message": f"Scheduled {len(created)} follow-ups",
        "follow_up_ids": [str(fu.id) for fu in created]
    }


@router.post("/{follow_up_id}/cancel")
async def cancel_follow_up(
    follow_up_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Cancel a pending follow-up."""
    follow_up = await db.get(FollowUp, follow_up_id)

    if not follow_up or follow_up.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    if follow_up.status != "pending":
        raise HTTPException(status_code=400, detail="Follow-up is not pending")

    follow_up.status = "cancelled"
    await db.commit()

    return {"message": "Follow-up cancelled"}


@router.post("/{follow_up_id}/send-now")
async def send_follow_up_now(
    follow_up_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Manually trigger a follow-up message immediately."""
    from app.services.whatsapp.sender import whatsapp_sender

    follow_up = await db.get(FollowUp, follow_up_id)

    if not follow_up or follow_up.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    if follow_up.status != "pending":
        raise HTTPException(status_code=400, detail="Follow-up is not pending")

    # Get client phone
    client = await db.get(Client, follow_up.client_id)
    if not client:
        raise HTTPException(status_code=400, detail="Client not found")

    # Send message
    result = await whatsapp_sender.send(client.phone, follow_up.message_template)

    if result.get("status") == "sent":
        follow_up.status = "sent"
        follow_up.sent_at = datetime.utcnow()
        await db.commit()
        return {"message": "Follow-up sent", "status": "sent"}
    else:
        follow_up.status = "failed"
        follow_up.error_message = result.get("message")
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to send: {result.get('message')}")


# ===========================================
# Protocol Endpoints
# ===========================================

@router.get("/protocols", response_model=list[ProtocolResponse])
async def list_protocols(
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """List all follow-up protocols for the clinic."""
    result = await db.execute(
        select(FollowUpProtocol)
        .where(FollowUpProtocol.clinic_id == current_user.clinic_id)
        .order_by(FollowUpProtocol.name)
    )
    protocols = result.scalars().all()

    return [
        ProtocolResponse(
            id=str(p.id),
            name=p.name,
            procedure_type=p.procedure_type,
            is_active=p.is_active,
            schedule_hours=p.schedule_hours or [],
            message_templates=p.message_templates or [],
            escalation_keywords=p.escalation_keywords or []
        )
        for p in protocols
    ]


@router.post("/protocols", response_model=ProtocolResponse)
async def create_protocol(
    request: CreateProtocolRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Create a new follow-up protocol."""
    protocol = FollowUpProtocol(
        clinic_id=current_user.clinic_id,
        name=request.name,
        procedure_type=request.procedure_type,
        is_active=True,
        schedule_hours=request.schedule_hours,
        message_templates=request.message_templates,
        escalation_keywords=request.escalation_keywords
    )

    db.add(protocol)
    await db.commit()
    await db.refresh(protocol)

    return ProtocolResponse(
        id=str(protocol.id),
        name=protocol.name,
        procedure_type=protocol.procedure_type,
        is_active=protocol.is_active,
        schedule_hours=protocol.schedule_hours or [],
        message_templates=protocol.message_templates or [],
        escalation_keywords=protocol.escalation_keywords or []
    )


@router.patch("/protocols/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(
    protocol_id: uuid.UUID,
    request: UpdateProtocolRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Update a follow-up protocol."""
    protocol = await db.get(FollowUpProtocol, protocol_id)

    if not protocol or protocol.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Protocol not found")

    if request.name is not None:
        protocol.name = request.name
    if request.is_active is not None:
        protocol.is_active = request.is_active
    if request.schedule_hours is not None:
        protocol.schedule_hours = request.schedule_hours
    if request.message_templates is not None:
        protocol.message_templates = request.message_templates
    if request.escalation_keywords is not None:
        protocol.escalation_keywords = request.escalation_keywords

    await db.commit()
    await db.refresh(protocol)

    return ProtocolResponse(
        id=str(protocol.id),
        name=protocol.name,
        procedure_type=protocol.procedure_type,
        is_active=protocol.is_active,
        schedule_hours=protocol.schedule_hours or [],
        message_templates=protocol.message_templates or [],
        escalation_keywords=protocol.escalation_keywords or []
    )


@router.delete("/protocols/{protocol_id}")
async def delete_protocol(
    protocol_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Delete a follow-up protocol."""
    protocol = await db.get(FollowUpProtocol, protocol_id)

    if not protocol or protocol.clinic_id != current_user.clinic_id:
        raise HTTPException(status_code=404, detail="Protocol not found")

    await db.delete(protocol)
    await db.commit()

    return {"message": "Protocol deleted"}
