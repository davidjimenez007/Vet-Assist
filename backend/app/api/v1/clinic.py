"""Clinic management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Clinic, Staff
from app.schemas.clinic import (
    ClinicResponse,
    ClinicUpdate,
    StaffCreate,
    StaffResponse,
    StaffUpdate,
)
from app.api.deps import CurrentUser, CurrentClinic, DBSession

router = APIRouter()


@router.get("", response_model=ClinicResponse)
async def get_clinic(
    current_clinic: CurrentClinic,
):
    """Get current clinic information."""
    return current_clinic


@router.patch("", response_model=ClinicResponse)
async def update_clinic(
    update_data: ClinicUpdate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Update clinic information."""
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        if value is not None:
            setattr(current_clinic, field, value)

    await db.commit()
    await db.refresh(current_clinic)

    return current_clinic


@router.get("/staff", response_model=list[StaffResponse])
async def list_staff(
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """List all staff members for the clinic."""
    result = await db.execute(
        select(Staff).where(Staff.clinic_id == current_clinic.id)
    )
    return result.scalars().all()


@router.post("/staff", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Create a new staff member."""
    staff = Staff(
        clinic_id=current_clinic.id,
        name=staff_data.name,
        role=staff_data.role,
        phone=staff_data.phone,
        email=staff_data.email,
        is_on_call=staff_data.is_on_call,
    )

    db.add(staff)
    await db.commit()
    await db.refresh(staff)

    return staff


@router.get("/staff/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: UUID,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Get a specific staff member."""
    result = await db.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.clinic_id == current_clinic.id,
        )
    )
    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    return staff


@router.patch("/staff/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: UUID,
    update_data: StaffUpdate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Update a staff member."""
    result = await db.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.clinic_id == current_clinic.id,
        )
    )
    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        if value is not None:
            setattr(staff, field, value)

    await db.commit()
    await db.refresh(staff)

    return staff


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: UUID,
    current_user: CurrentUser,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Delete a staff member."""
    # Prevent deleting yourself
    if staff_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete yourself",
        )

    result = await db.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.clinic_id == current_clinic.id,
        )
    )
    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    await db.delete(staff)
    await db.commit()
