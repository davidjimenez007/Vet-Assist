"""Demo request endpoints."""

import asyncio
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, desc

from app.models.demo_request import DemoRequest
from app.api.deps import CurrentUser, DBSession
from app.services.email import notify_new_demo_request

logger = logging.getLogger(__name__)

router = APIRouter()


class DemoRequestCreate(BaseModel):
    """Schema for creating a demo request (public, no auth)."""

    clinic_name: str
    contact_name: str
    email: EmailStr
    phone: str
    clinic_size: Optional[str] = None
    preferred_time: Optional[str] = None
    message: Optional[str] = None


class DemoRequestResponse(BaseModel):
    """Schema for demo request response."""

    id: UUID
    clinic_name: str
    contact_name: str
    email: str
    phone: str
    clinic_size: Optional[str] = None
    preferred_time: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: str

    class Config:
        from_attributes = True


class DemoRequestStatusUpdate(BaseModel):
    """Schema for updating demo request status."""

    status: str  # pending, contacted, converted, dismissed


@router.post("", status_code=201)
async def create_demo_request(
    data: DemoRequestCreate,
    db: DBSession,
    background_tasks: BackgroundTasks,
):
    """Create a demo request (public endpoint, no auth required)."""
    demo_request = DemoRequest(
        clinic_name=data.clinic_name,
        contact_name=data.contact_name,
        email=data.email,
        phone=data.phone,
        clinic_size=data.clinic_size,
        preferred_time=data.preferred_time,
        message=data.message,
    )

    db.add(demo_request)
    await db.commit()
    await db.refresh(demo_request)

    # Send email notification in background
    background_tasks.add_task(
        notify_new_demo_request,
        clinic_name=data.clinic_name,
        contact_name=data.contact_name,
        email=data.email,
        phone=data.phone,
        clinic_size=data.clinic_size,
        preferred_time=data.preferred_time,
        message=data.message,
    )

    return {
        "success": True,
        "message": "Solicitud de demo recibida correctamente",
        "id": str(demo_request.id),
    }


@router.get("", response_model=list[DemoRequestResponse])
async def list_demo_requests(
    current_user: CurrentUser,
    db: DBSession,
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
):
    """List demo requests (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    query = select(DemoRequest)

    if status:
        query = query.where(DemoRequest.status == status)

    query = query.order_by(desc(DemoRequest.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    requests = result.scalars().all()

    return [
        DemoRequestResponse(
            id=r.id,
            clinic_name=r.clinic_name,
            contact_name=r.contact_name,
            email=r.email,
            phone=r.phone,
            clinic_size=r.clinic_size,
            preferred_time=r.preferred_time,
            message=r.message,
            status=r.status,
            created_at=r.created_at.isoformat(),
        )
        for r in requests
    ]


@router.patch("/{request_id}")
async def update_demo_request_status(
    request_id: UUID,
    update_data: DemoRequestStatusUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update demo request status (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(DemoRequest).where(DemoRequest.id == request_id)
    )
    demo_request = result.scalar_one_or_none()

    if not demo_request:
        raise HTTPException(status_code=404, detail="Demo request not found")

    valid_statuses = ["pending", "contacted", "converted", "dismissed"]
    if update_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    demo_request.status = update_data.status
    await db.commit()

    return {"success": True, "status": demo_request.status}
