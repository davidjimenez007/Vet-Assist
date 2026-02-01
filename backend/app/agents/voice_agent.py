"""Voice agent for TwiML generation and voice interaction."""

from typing import Optional

from app.services.twilio_client import TwilioService
from app.services.ai import AIService


class VoiceAgent:
    """Agent for handling voice call interactions."""

    def __init__(
        self,
        twilio_service: Optional[TwilioService] = None,
        ai_service: Optional[AIService] = None,
    ):
        self.twilio = twilio_service or TwilioService()
        self.ai = ai_service or AIService()

    def create_greeting(
        self, clinic_name: str, gather_action: str
    ) -> str:
        """Create TwiML greeting for incoming call."""
        greeting = (
            f"{clinic_name}, buenos días. Soy el asistente virtual. "
            "¿En qué puedo ayudarle hoy?"
        )

        return self.twilio.create_greeting_twiml(
            message=greeting,
            gather_action=gather_action,
        )

    def create_response(
        self,
        message: str,
        gather_action: Optional[str] = None,
        end_call: bool = False,
    ) -> str:
        """Create TwiML response for voice interaction."""
        return self.twilio.create_response_twiml(
            message=message,
            gather_action=gather_action,
            end_call=end_call,
        )

    def create_transfer(
        self,
        transfer_to: str,
        fallback_message: Optional[str] = None,
    ) -> str:
        """Create TwiML for call transfer."""
        if not fallback_message:
            fallback_message = (
                "El doctor no pudo contestar en este momento. "
                "Le estoy enviando una alerta urgente y lo contactarán en los próximos minutos."
            )

        return self.twilio.create_transfer_twiml(
            transfer_to=transfer_to,
            fallback_message=fallback_message,
        )

    def create_hold_message(self) -> str:
        """Create TwiML for hold message during processing."""
        return self.twilio.create_response_twiml(
            message="Un momento por favor...",
            gather_action=None,
            end_call=False,
        )

    def format_slots_for_voice(self, slots: list[dict]) -> str:
        """Format time slots for voice response."""
        if not slots:
            return "No hay disponibilidad en este momento."

        formatted = []
        for i, slot in enumerate(slots[:3], 1):
            time_str = self._format_time_for_voice(slot["start"])
            formatted.append(time_str)

        if len(formatted) == 1:
            return f"Tenemos disponibilidad a las {formatted[0]}."
        elif len(formatted) == 2:
            return f"Tenemos disponibilidad a las {formatted[0]} y a las {formatted[1]}."
        else:
            return f"Tenemos disponibilidad a las {', las '.join(formatted[:-1])}, y a las {formatted[-1]}."

    def _format_time_for_voice(self, time_str: str) -> str:
        """Format time string for natural voice output."""
        hour, minute = map(int, time_str.split(":"))

        if hour < 12:
            period = "de la mañana"
        elif hour < 18:
            period = "de la tarde"
        else:
            period = "de la noche"

        display_hour = hour if hour <= 12 else hour - 12

        if minute == 0:
            return f"{display_hour} {period}"
        elif minute == 30:
            return f"{display_hour} y media {period}"
        else:
            return f"{display_hour} y {minute} {period}"

    def format_confirmation_for_voice(
        self,
        pet_name: Optional[str],
        pet_type: str,
        appointment_type: str,
        date_str: str,
        time_str: str,
    ) -> str:
        """Format booking confirmation for voice."""
        pet_ref = pet_name or f"su {self._translate_pet_type(pet_type)}"

        return (
            f"Perfecto. Su cita de {self._translate_appointment_type(appointment_type)} "
            f"para {pet_ref} está confirmada para el {date_str} a las {time_str}. "
            "Le enviaremos un mensaje de confirmación."
        )

    def _translate_pet_type(self, pet_type: str) -> str:
        """Translate pet type to Spanish."""
        translations = {
            "dog": "perro",
            "cat": "gato",
            "other": "mascota",
        }
        return translations.get(pet_type.lower(), pet_type)

    def _translate_appointment_type(self, appointment_type: str) -> str:
        """Translate appointment type to Spanish."""
        translations = {
            "consultation": "consulta",
            "vaccination": "vacunación",
            "surgery": "cirugía",
            "grooming": "peluquería",
            "emergency": "emergencia",
        }
        return translations.get(appointment_type.lower(), appointment_type)

    def create_goodbye(self, booked: bool = False) -> str:
        """Create farewell TwiML."""
        if booked:
            message = (
                "Gracias por llamar. Le enviaremos un recordatorio. "
                "¡Que tenga un excelente día!"
            )
        else:
            message = "Gracias por llamar. ¡Que tenga un excelente día!"

        return self.twilio.create_response_twiml(
            message=message,
            end_call=True,
        )
