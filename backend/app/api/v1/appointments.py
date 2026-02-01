"""Appointment management endpoints."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Appointment, Client, Pet, Staff
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    AvailableSlotsResponse,
    BookingResult,
)
from app.services.calendar import CalendarService
from app.api.deps import CurrentClinic, DBSession

router = APIRouter()


def appointment_to_response(apt: Appointment) -> AppointmentResponse:
    """Convert appointment model to response schema."""
    return AppointmentResponse(
        id=apt.id,
        clinic_id=apt.clinic_id,
        client_id=apt.client_id,
        pet_id=apt.pet_id,
        staff_id=apt.staff_id,
        start_time=apt.start_time,
        end_time=apt.end_time,
        duration_minutes=apt.duration_minutes,
        appointment_type=apt.appointment_type,
        reason=apt.reason,
        status=apt.status,
        source=apt.source,
        notes=apt.notes,
        created_at=apt.created_at,
        client_name=apt.client.name if apt.client else None,
        client_phone=apt.client.phone if apt.client else None,
        pet_name=apt.pet.name if apt.pet else None,
        pet_species=apt.pet.species if apt.pet else None,
        staff_name=apt.staff.name if apt.staff else None,
    )


@router.get("", response_model=list[AppointmentResponse])
async def list_appointments(
    current_clinic: CurrentClinic,
    db: DBSession,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    staff_id: Optional[UUID] = Query(None),
):
    """List appointments with optional filters."""
    query = (
        select(Appointment)
        .where(Appointment.clinic_id == current_clinic.id)
        .options(
            selectinload(Appointment.client),
            selectinload(Appointment.pet),
            selectinload(Appointment.staff),
        )
    )

    if start_date:
        query = query.where(Appointment.start_time >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.where(Appointment.start_time <= datetime.combine(end_date, datetime.max.time()))

    if status:
        query = query.where(Appointment.status == status)

    if staff_id:
        query = query.where(Appointment.staff_id == staff_id)

    query = query.order_by(Appointment.start_time)

    result = await db.execute(query)
    appointments = result.scalars().all()

    return [appointment_to_response(apt) for apt in appointments]


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Create a new appointment."""
    calendar_service = CalendarService(db)

    result = await calendar_service.book_appointment(
        clinic_id=current_clinic.id,
        appointment_data=appointment_data,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": result.error,
                "alternative_slots": [s.model_dump() for s in result.alternative_slots] if result.alternative_slots else [],
            },
        )

    # Get the created appointment with relationships
    apt_result = await db.execute(
        select(Appointment)
        .where(Appointment.clinic_id == current_clinic.id)
        .options(
            selectinload(Appointment.client),
            selectinload(Appointment.pet),
            selectinload(Appointment.staff),
        )
        .order_by(Appointment.created_at.desc())
        .limit(1)
    )
    appointment = apt_result.scalar_one()

    return appointment_to_response(appointment)


@router.get("/slots/available", response_model=AvailableSlotsResponse)
async def get_available_slots(
    current_clinic: CurrentClinic,
    db: DBSession,
    target_date: date = Query(..., alias="date"),
    duration: int = Query(30),
    staff_id: Optional[UUID] = Query(None),
):
    """Get available time slots for a date."""
    calendar_service = CalendarService(db)

    slots = await calendar_service.find_available_slots(
        clinic_id=current_clinic.id,
        target_date=target_date,
        duration_minutes=duration,
        staff_id=staff_id,
    )

    next_available = await calendar_service.get_next_available(
        clinic_id=current_clinic.id,
        duration_minutes=duration,
    )

    return AvailableSlotsResponse(
        date=target_date,
        available_slots=slots,
        next_available=next_available,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Get a specific appointment."""
    result = await db.execute(
        select(Appointment)
        .where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_clinic.id,
        )
        .options(
            selectinload(Appointment.client),
            selectinload(Appointment.pet),
            selectinload(Appointment.staff),
        )
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return appointment_to_response(appointment)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    update_data: AppointmentUpdate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Update an appointment."""
    result = await db.execute(
        select(Appointment)
        .where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_clinic.id,
        )
        .options(
            selectinload(Appointment.client),
            selectinload(Appointment.pet),
            selectinload(Appointment.staff),
        )
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        if value is not None:
            setattr(appointment, field, value)

    await db.commit()
    await db.refresh(appointment)

    return appointment_to_response(appointment)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: UUID,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Delete (cancel) an appointment."""
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == current_clinic.id,
        )
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Soft delete by setting status to cancelled
    appointment.status = "cancelled"
    await db.commit()
