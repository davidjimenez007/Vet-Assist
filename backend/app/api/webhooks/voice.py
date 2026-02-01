"""Twilio voice webhooks."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Form, Depends, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Clinic
from app.agents.orchestrator import Orchestrator

router = APIRouter()


async def get_clinic_by_called_number(
    to: str, db: AsyncSession
) -> Optional[Clinic]:
    """Get clinic by the phone number that was called."""
    # Normalize phone number
    phone = to.replace("whatsapp:", "").strip()

    result = await db.execute(
        select(Clinic).where(Clinic.phone == phone)
    )
    return result.scalar_one_or_none()


@router.post("/incoming")
async def voice_incoming(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming voice call from Twilio."""
    # Find clinic by called number
    clinic = await get_clinic_by_called_number(To, db)

    if not clinic:
        # Return a generic message if clinic not found
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Mia-Neural" language="es-CO">
        Lo sentimos, este número no está disponible. Por favor intente más tarde.
    </Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Create orchestrator and handle call
    orchestrator = Orchestrator(db, clinic)
    twiml = await orchestrator.handle_voice_incoming(
        call_sid=CallSid,
        caller_phone=From,
    )

    return Response(content=twiml, media_type="application/xml")


@router.post("/gather")
async def voice_gather(
    conversation_id: UUID,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    SpeechResult: str = Form(None),
    Confidence: float = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle speech input from Twilio Gather."""
    if not SpeechResult:
        # No speech detected, prompt again
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="/webhooks/voice/gather?conversation_id={conversation_id}"
            method="POST" language="es-CO" speechTimeout="auto" speechModel="phone_call">
        <Say voice="Polly.Mia-Neural" language="es-CO">
            Lo siento, no pude escucharlo. ¿Puede repetir por favor?
        </Say>
    </Gather>
    <Redirect>/webhooks/voice/gather?conversation_id={conversation_id}</Redirect>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Get clinic
    clinic = await get_clinic_by_called_number(To, db)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    # Process speech input
    orchestrator = Orchestrator(db, clinic)
    twiml = await orchestrator.handle_voice_input(
        conversation_id=conversation_id,
        speech_result=SpeechResult,
        caller_phone=From,
    )

    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def voice_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: int = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle call status updates from Twilio."""
    # Log call status for analytics
    # In a production system, you would update the conversation record

    return {"status": "ok", "call_status": CallStatus}


@router.post("/transfer-status")
async def transfer_status(
    CallSid: str = Form(...),
    DialCallStatus: str = Form(...),
    DialCallDuration: int = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle transfer call status."""
    if DialCallStatus in ["no-answer", "busy", "failed"]:
        # Transfer failed, send alert
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Mia-Neural" language="es-CO">
        El doctor no pudo contestar. Le hemos enviado una alerta urgente y lo contactarán
        en los próximos minutos. El número de emergencias de la clínica le será enviado por mensaje.
    </Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Transfer successful
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response/>',
        media_type="application/xml",
    )


@router.post("/transcription")
async def voice_transcription(
    TranscriptionSid: str = Form(...),
    TranscriptionText: str = Form(...),
    TranscriptionStatus: str = Form(...),
    CallSid: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle transcription callback (for async transcription)."""
    # Store transcription if needed
    return {"status": "ok"}
