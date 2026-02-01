"""Analytics endpoints."""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import select, func, and_

from app.models import Appointment, Conversation
from app.api.deps import CurrentClinic, DBSession

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(
    current_clinic: CurrentClinic,
    db: DBSession,
    period: str = Query("week", regex="^(day|week|month)$"),
):
    """Get analytics summary for the specified period."""
    # Calculate date range
    today = date.today()

    if period == "day":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    else:  # month
        start_date = today - timedelta(days=30)

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(today, datetime.max.time())

    # Get appointment stats
    appointments_result = await db.execute(
        select(func.count(Appointment.id))
        .where(
            Appointment.clinic_id == current_clinic.id,
            Appointment.created_at >= start_datetime,
            Appointment.created_at <= end_datetime,
        )
    )
    total_appointments = appointments_result.scalar() or 0

    # Appointments by status
    status_result = await db.execute(
        select(Appointment.status, func.count(Appointment.id))
        .where(
            Appointment.clinic_id == current_clinic.id,
            Appointment.start_time >= start_datetime,
            Appointment.start_time <= end_datetime,
        )
        .group_by(Appointment.status)
    )
    appointments_by_status = {row[0]: row[1] for row in status_result.fetchall()}

    # Appointments by source
    source_result = await db.execute(
        select(Appointment.source, func.count(Appointment.id))
        .where(
            Appointment.clinic_id == current_clinic.id,
            Appointment.created_at >= start_datetime,
            Appointment.created_at <= end_datetime,
        )
        .group_by(Appointment.source)
    )
    appointments_by_source = {row[0]: row[1] for row in source_result.fetchall()}

    # Get conversation stats
    conversations_result = await db.execute(
        select(func.count(Conversation.id))
        .where(
            Conversation.clinic_id == current_clinic.id,
            Conversation.started_at >= start_datetime,
            Conversation.started_at <= end_datetime,
        )
    )
    total_conversations = conversations_result.scalar() or 0

    # Conversations by channel
    channel_result = await db.execute(
        select(Conversation.channel, func.count(Conversation.id))
        .where(
            Conversation.clinic_id == current_clinic.id,
            Conversation.started_at >= start_datetime,
            Conversation.started_at <= end_datetime,
        )
        .group_by(Conversation.channel)
    )
    conversations_by_channel = {row[0]: row[1] for row in channel_result.fetchall()}

    # Conversations by outcome
    outcome_result = await db.execute(
        select(Conversation.outcome, func.count(Conversation.id))
        .where(
            Conversation.clinic_id == current_clinic.id,
            Conversation.started_at >= start_datetime,
            Conversation.started_at <= end_datetime,
            Conversation.outcome.isnot(None),
        )
        .group_by(Conversation.outcome)
    )
    conversations_by_outcome = {row[0]: row[1] for row in outcome_result.fetchall()}

    # Emergencies detected
    emergencies_result = await db.execute(
        select(func.count(Conversation.id))
        .where(
            Conversation.clinic_id == current_clinic.id,
            Conversation.started_at >= start_datetime,
            Conversation.started_at <= end_datetime,
            Conversation.intent == "EMERGENCY",
        )
    )
    emergencies_detected = emergencies_result.scalar() or 0

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": today.isoformat(),
        "appointments": {
            "total": total_appointments,
            "by_status": appointments_by_status,
            "by_source": appointments_by_source,
        },
        "conversations": {
            "total": total_conversations,
            "by_channel": conversations_by_channel,
            "by_outcome": conversations_by_outcome,
        },
        "emergencies_detected": emergencies_detected,
    }


@router.get("/today")
async def get_today_stats(
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Get today's quick stats for dashboard."""
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    # Today's appointments
    today_appointments = await db.execute(
        select(func.count(Appointment.id))
        .where(
            Appointment.clinic_id == current_clinic.id,
            Appointment.start_time >= start_of_day,
            Appointment.start_time <= end_of_day,
            Appointment.status != "cancelled",
        )
    )

    # Today's calls
    today_calls = await db.execute(
        select(func.count(Conversation.id))
        .where(
            Conversation.clinic_id == current_clinic.id,
            Conversation.started_at >= start_of_day,
            Conversation.started_at <= end_of_day,
            Conversation.channel == "voice",
        )
    )

    # Today's messages
    today_messages = await db.execute(
        select(func.count(Conversation.id))
        .where(
            Conversation.clinic_id == current_clinic.id,
            Conversation.started_at >= start_of_day,
            Conversation.started_at <= end_of_day,
            Conversation.channel == "whatsapp",
        )
    )

    # Active emergencies (today's escalated conversations)
    active_emergencies = await db.execute(
        select(func.count(Conversation.id))
        .where(
            Conversation.clinic_id == current_clinic.id,
            Conversation.started_at >= start_of_day,
            Conversation.started_at <= end_of_day,
            Conversation.status == "escalated",
        )
    )

    return {
        "date": today.isoformat(),
        "appointments_today": today_appointments.scalar() or 0,
        "calls_today": today_calls.scalar() or 0,
        "messages_today": today_messages.scalar() or 0,
        "active_emergencies": active_emergencies.scalar() or 0,
    }
