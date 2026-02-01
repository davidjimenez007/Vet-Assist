"""WhatsApp message sender service."""

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppSender:
    """Sends messages via WhatsApp Business API (Twilio)."""

    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = settings.twilio_whatsapp_number
        self.enabled = bool(self.account_sid and self.auth_token)

    async def send(
        self,
        to_phone: str,
        message: str,
        media_url: Optional[str] = None
    ) -> dict:
        """
        Send a WhatsApp message.

        Args:
            to_phone: Recipient phone number (with country code, e.g., +573001234567)
            message: Message text
            media_url: Optional URL to media file

        Returns:
            dict with status and message_sid
        """
        if not self.enabled:
            logger.warning("WhatsApp sending disabled - no Twilio credentials")
            return {
                "status": "disabled",
                "message_sid": None,
                "message": "WhatsApp sending is disabled"
            }

        # Format numbers for WhatsApp
        to_whatsapp = f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone
        from_whatsapp = f"whatsapp:{self.from_number}" if not self.from_number.startswith("whatsapp:") else self.from_number

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

        data = {
            "To": to_whatsapp,
            "From": from_whatsapp,
            "Body": message,
        }

        if media_url:
            data["MediaUrl"] = media_url

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(self.account_sid, self.auth_token),
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"WhatsApp sent to {to_phone}: {result.get('sid')}")
                    return {
                        "status": "sent",
                        "message_sid": result.get("sid"),
                        "message": "Message sent successfully"
                    }
                else:
                    logger.error(f"WhatsApp send failed: {response.status_code} - {response.text}")
                    return {
                        "status": "failed",
                        "message_sid": None,
                        "message": f"Failed to send: {response.status_code}"
                    }

        except Exception as e:
            logger.exception(f"WhatsApp send error: {e}")
            return {
                "status": "error",
                "message_sid": None,
                "message": str(e)
            }

    async def send_template(
        self,
        to_phone: str,
        template_sid: str,
        variables: Optional[dict] = None
    ) -> dict:
        """
        Send a WhatsApp template message.
        Templates are pre-approved messages for business communications.

        Args:
            to_phone: Recipient phone number
            template_sid: Twilio template SID
            variables: Template variables

        Returns:
            dict with status and message_sid
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message_sid": None,
                "message": "WhatsApp sending is disabled"
            }

        to_whatsapp = f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone
        from_whatsapp = f"whatsapp:{self.from_number}" if not self.from_number.startswith("whatsapp:") else self.from_number

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

        data = {
            "To": to_whatsapp,
            "From": from_whatsapp,
            "ContentSid": template_sid,
        }

        if variables:
            data["ContentVariables"] = str(variables)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(self.account_sid, self.auth_token),
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    return {
                        "status": "sent",
                        "message_sid": result.get("sid"),
                        "message": "Template sent successfully"
                    }
                else:
                    logger.error(f"WhatsApp template send failed: {response.status_code}")
                    return {
                        "status": "failed",
                        "message_sid": None,
                        "message": f"Failed to send: {response.status_code}"
                    }

        except Exception as e:
            logger.exception(f"WhatsApp template send error: {e}")
            return {
                "status": "error",
                "message_sid": None,
                "message": str(e)
            }


# Singleton instance
whatsapp_sender = WhatsAppSender()
