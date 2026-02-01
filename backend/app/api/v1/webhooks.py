"""Webhook handlers for external services."""

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models import Clinic
from app.services.whatsapp.engine import ConversationEngine

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.get("/whatsapp")
async def whatsapp_webhook_verify(
    request: Request,
):
    """
    Webhook verification endpoint for Twilio/WhatsApp.
    Twilio sends a GET request to verify the webhook URL.
    """
    # For Twilio, verification is done differently
    # This endpoint just needs to respond with 200
    return Response(content="OK", status_code=200)


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle incoming WhatsApp messages from Twilio.

    Twilio sends POST requests with form data containing:
    - From: Sender's phone number (whatsapp:+1234567890)
    - To: Your Twilio number (whatsapp:+0987654321)
    - Body: Message text
    - MessageSid: Unique message ID
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()

        from_number = form_data.get("From", "")
        to_number = form_data.get("To", "")
        body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")

        # Log incoming message
        logger.info(f"WhatsApp message from {from_number}: {body[:50]}...")

        # Extract phone number (remove whatsapp: prefix)
        phone = from_number.replace("whatsapp:", "").strip()
        clinic_number = to_number.replace("whatsapp:", "").strip()

        if not phone or not body:
            logger.warning("Missing phone or body in webhook")
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                media_type="application/xml"
            )

        # Find clinic by WhatsApp number
        clinic = await _get_clinic_by_whatsapp(db, clinic_number)

        if not clinic:
            logger.warning(f"No clinic found for WhatsApp number: {clinic_number}")
            # Try to get default/first clinic for development
            result = await db.execute(select(Clinic).limit(1))
            clinic = result.scalar_one_or_none()

        if not clinic:
            logger.error("No clinic found to handle message")
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                media_type="application/xml"
            )

        # Process message through conversation engine
        engine = ConversationEngine(db)
        result = await engine.process_incoming_message(
            clinic_id=clinic.id,
            phone=phone,
            message_text=body,
            external_id=message_sid
        )

        logger.info(f"Conversation result: state={result.get('state')}, action={result.get('action')}")

        # Return TwiML response (empty - we send messages via API)
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )

    except Exception as e:
        logger.exception(f"Error processing WhatsApp webhook: {e}")
        # Return empty TwiML to prevent Twilio retries
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )


@router.post("/whatsapp/status")
async def whatsapp_status_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle WhatsApp message status callbacks from Twilio.

    Twilio sends status updates when messages are:
    - queued
    - sent
    - delivered
    - read
    - failed
    """
    try:
        form_data = await request.form()

        message_sid = form_data.get("MessageSid", "")
        status = form_data.get("MessageStatus", "")
        error_code = form_data.get("ErrorCode")
        error_message = form_data.get("ErrorMessage")

        logger.info(f"WhatsApp status update: {message_sid} -> {status}")

        if error_code:
            logger.error(f"WhatsApp error: {error_code} - {error_message}")

        # TODO: Update message status in database if needed

        return Response(content="OK", status_code=200)

    except Exception as e:
        logger.exception(f"Error processing status callback: {e}")
        return Response(content="OK", status_code=200)


async def _get_clinic_by_whatsapp(
    db: AsyncSession,
    whatsapp_number: str
) -> Optional[Clinic]:
    """Find clinic by WhatsApp number."""
    # Try exact match first
    result = await db.execute(
        select(Clinic)
        .where(Clinic.whatsapp_number == whatsapp_number)
    )
    clinic = result.scalar_one_or_none()

    if clinic:
        return clinic

    # Try with different formats
    # Remove + prefix
    if whatsapp_number.startswith("+"):
        number_no_plus = whatsapp_number[1:]
        result = await db.execute(
            select(Clinic)
            .where(Clinic.whatsapp_number == number_no_plus)
        )
        clinic = result.scalar_one_or_none()
        if clinic:
            return clinic

    # Try matching phone field
    result = await db.execute(
        select(Clinic)
        .where(Clinic.phone == whatsapp_number)
    )
    return result.scalar_one_or_none()


def verify_twilio_signature(
    request: Request,
    signature: str,
    url: str,
    params: dict
) -> bool:
    """Verify that a request came from Twilio."""
    if not settings.twilio_auth_token:
        return True  # Skip verification if no auth token configured

    # Build the string to sign
    s = url
    for key in sorted(params.keys()):
        s += key + params[key]

    # Compute the signature
    computed = hmac.new(
        settings.twilio_auth_token.encode(),
        s.encode(),
        hashlib.sha1
    ).digest()

    import base64
    computed_b64 = base64.b64encode(computed).decode()

    return hmac.compare_digest(computed_b64, signature)
