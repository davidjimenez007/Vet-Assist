"""Twilio WhatsApp webhooks."""

from typing import Optional

from fastapi import APIRouter, Form, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Clinic
from app.agents.orchestrator import Orchestrator
from app.services.twilio_client import TwilioService

router = APIRouter()


async def get_clinic_by_whatsapp_number(
    to: str, db: AsyncSession
) -> Optional[Clinic]:
    """Get clinic by WhatsApp number."""
    # Remove whatsapp: prefix if present
    phone = to.replace("whatsapp:", "").strip()

    # Try whatsapp_number first, then regular phone
    result = await db.execute(
        select(Clinic).where(
            (Clinic.whatsapp_number == phone) | (Clinic.phone == phone)
        )
    )
    return result.scalar_one_or_none()


@router.post("/incoming")
async def whatsapp_incoming(
    MessageSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    NumMedia: int = Form(0),
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming WhatsApp message."""
    # Clean phone numbers
    sender_phone = From.replace("whatsapp:", "").strip()

    # Find clinic
    clinic = await get_clinic_by_whatsapp_number(To, db)

    if not clinic:
        # Return empty TwiML - message won't be replied to
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response/>',
            media_type="application/xml",
        )

    # Handle media messages
    if NumMedia > 0:
        # For now, we don't process media
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
        Gracias por tu mensaje. Por el momento solo puedo procesar texto.
        ¿En qué puedo ayudarte?
    </Message>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Process message
    orchestrator = Orchestrator(db, clinic)
    response_message = await orchestrator.handle_whatsapp_message(
        message_sid=MessageSid,
        sender_phone=sender_phone,
        message_body=Body,
    )

    # Return TwiML response
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_message}</Message>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def whatsapp_status(
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    To: str = Form(None),
    ErrorCode: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle WhatsApp message status updates."""
    # Log status for analytics
    # Statuses: queued, sent, delivered, read, failed, undelivered

    if MessageStatus in ["failed", "undelivered"]:
        # Log error for review
        print(f"WhatsApp message {MessageSid} failed: {ErrorCode}")

    return {"status": "ok", "message_status": MessageStatus}


@router.post("/fallback")
async def whatsapp_fallback(
    MessageSid: str = Form(None),
    From: str = Form(None),
    Body: str = Form(None),
    ErrorCode: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Fallback handler for webhook errors."""
    # Log the error
    print(f"WhatsApp fallback triggered: {ErrorCode}")

    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
        Lo sentimos, estamos experimentando dificultades técnicas.
        Por favor intenta de nuevo más tarde o llama directamente a la clínica.
    </Message>
</Response>"""

    return Response(content=twiml, media_type="application/xml")
