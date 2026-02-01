"""Twilio client wrapper for voice and messaging."""

from typing import Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.config import settings


class TwilioService:
    """Service for Twilio voice and messaging operations."""

    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.phone_number = settings.twilio_phone_number
        self.whatsapp_number = settings.twilio_whatsapp_number

        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None

    def create_greeting_twiml(
        self, message: str, gather_action: str, language: str = "es-CO"
    ) -> str:
        """Create TwiML for greeting with speech input."""
        response = VoiceResponse()

        gather = Gather(
            input="speech",
            action=gather_action,
            method="POST",
            language=language,
            speech_timeout="auto",
            speech_model="phone_call",
        )
        gather.say(message, voice="Polly.Mia-Neural", language=language)

        response.append(gather)

        # If no input, repeat
        response.redirect(gather_action)

        return str(response)

    def create_response_twiml(
        self,
        message: str,
        gather_action: Optional[str] = None,
        end_call: bool = False,
        language: str = "es-CO",
    ) -> str:
        """Create TwiML for a response, optionally gathering more input."""
        response = VoiceResponse()

        if gather_action and not end_call:
            gather = Gather(
                input="speech",
                action=gather_action,
                method="POST",
                language=language,
                speech_timeout="auto",
                speech_model="phone_call",
            )
            gather.say(message, voice="Polly.Mia-Neural", language=language)
            response.append(gather)
        else:
            response.say(message, voice="Polly.Mia-Neural", language=language)

        if end_call:
            response.hangup()

        return str(response)

    def create_transfer_twiml(
        self, transfer_to: str, fallback_message: str
    ) -> str:
        """Create TwiML for call transfer."""
        response = VoiceResponse()

        response.say(
            "Voy a transferir su llamada. Por favor no cuelgue.",
            voice="Polly.Mia-Neural",
            language="es-CO",
        )

        response.dial(
            transfer_to,
            timeout=30,
            action="/webhooks/voice/transfer-status",
            method="POST",
        )

        # Fallback if transfer fails
        response.say(fallback_message, voice="Polly.Mia-Neural", language="es-CO")

        return str(response)

    async def send_sms(self, to: str, message: str) -> bool:
        """Send an SMS message."""
        if not self.client:
            print(f"[SMS Mock] To: {to}, Message: {message}")
            return True

        try:
            self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to,
            )
            return True
        except Exception as e:
            print(f"SMS send error: {e}")
            return False

    async def send_whatsapp(self, to: str, message: str) -> bool:
        """Send a WhatsApp message."""
        if not self.client:
            print(f"[WhatsApp Mock] To: {to}, Message: {message}")
            return True

        try:
            # WhatsApp numbers need the whatsapp: prefix
            whatsapp_to = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
            whatsapp_from = f"whatsapp:{self.whatsapp_number}"

            self.client.messages.create(
                body=message,
                from_=whatsapp_from,
                to=whatsapp_to,
            )
            return True
        except Exception as e:
            print(f"WhatsApp send error: {e}")
            return False

    async def initiate_call(self, to: str, url: str) -> Optional[str]:
        """Initiate an outbound call."""
        if not self.client:
            print(f"[Call Mock] To: {to}, URL: {url}")
            return "mock_call_sid"

        try:
            call = self.client.calls.create(
                url=url,
                to=to,
                from_=self.phone_number,
            )
            return call.sid
        except Exception as e:
            print(f"Call initiate error: {e}")
            return None

    def validate_request(
        self, signature: str, url: str, params: dict
    ) -> bool:
        """Validate that a request came from Twilio."""
        if not self.client:
            return True  # Skip validation in development

        from twilio.request_validator import RequestValidator

        validator = RequestValidator(self.auth_token)
        return validator.validate(url, params, signature)
