"""Settings management endpoints."""

from fastapi import APIRouter

from app.schemas.clinic import ClinicUpdate, WorkingHours, EscalationContact
from app.api.deps import CurrentClinic, DBSession

router = APIRouter()


@router.get("")
async def get_settings(
    current_clinic: CurrentClinic,
):
    """Get all clinic settings."""
    return {
        "working_hours": current_clinic.working_hours,
        "appointment_durations": current_clinic.appointment_duration_minutes,
        "escalation_contacts": current_clinic.escalation_contacts,
        "timezone": current_clinic.timezone,
        "custom_settings": current_clinic.settings,
    }


@router.patch("")
async def update_settings(
    update_data: ClinicUpdate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Update clinic settings."""
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        if value is not None:
            setattr(current_clinic, field, value)

    await db.commit()
    await db.refresh(current_clinic)

    return {
        "working_hours": current_clinic.working_hours,
        "appointment_durations": current_clinic.appointment_duration_minutes,
        "escalation_contacts": current_clinic.escalation_contacts,
        "timezone": current_clinic.timezone,
        "custom_settings": current_clinic.settings,
    }


@router.get("/hours")
async def get_working_hours(
    current_clinic: CurrentClinic,
):
    """Get working hours configuration."""
    return current_clinic.working_hours


@router.patch("/hours")
async def update_working_hours(
    hours: dict[str, WorkingHours | None],
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Update working hours."""
    # Merge with existing hours
    existing = current_clinic.working_hours or {}
    for day, value in hours.items():
        if value is None:
            existing[day] = None
        else:
            existing[day] = value.model_dump()

    current_clinic.working_hours = existing
    await db.commit()

    return current_clinic.working_hours


@router.get("/durations")
async def get_appointment_durations(
    current_clinic: CurrentClinic,
):
    """Get appointment duration settings."""
    return current_clinic.appointment_duration_minutes


@router.patch("/durations")
async def update_appointment_durations(
    durations: dict[str, int],
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Update appointment durations."""
    existing = current_clinic.appointment_duration_minutes or {}
    existing.update(durations)

    current_clinic.appointment_duration_minutes = existing
    await db.commit()

    return current_clinic.appointment_duration_minutes


@router.get("/escalation")
async def get_escalation_contacts(
    current_clinic: CurrentClinic,
):
    """Get escalation contacts."""
    return current_clinic.escalation_contacts


@router.put("/escalation")
async def update_escalation_contacts(
    contacts: list[EscalationContact],
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Update escalation contacts."""
    current_clinic.escalation_contacts = [c.model_dump() for c in contacts]
    await db.commit()

    return current_clinic.escalation_contacts
