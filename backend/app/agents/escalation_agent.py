"""Escalation agent for emergency handling."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.services.notification import NotificationService
from app.services.ai import AIService
from app.services.twilio_client import TwilioService
from app.models import Clinic


@dataclass
class EscalationResult:
    """Result of an escalation attempt."""

    success: bool
    action_taken: str
    contacts_notified: list[dict]
    transfer_attempted: bool
    transfer_successful: bool
    response_message: str


class EscalationAgent:
    """Agent for handling emergency escalations."""

    def __init__(
        self,
        notification_service: Optional[NotificationService] = None,
        twilio_service: Optional[TwilioService] = None,
        ai_service: Optional[AIService] = None,
    ):
        self.notifications = notification_service or NotificationService()
        self.twilio = twilio_service or TwilioService()
        self.ai = ai_service or AIService()

    async def handle_emergency(
        self,
        clinic: Clinic,
        caller_phone: str,
        urgency_level: str,
        symptoms: list[str],
        channel: str = "voice",
    ) -> EscalationResult:
        """Handle an emergency situation."""
        # Get escalation contacts
        contacts = clinic.escalation_contacts or []

        if not contacts:
            return EscalationResult(
                success=False,
                action_taken="no_contacts",
                contacts_notified=[],
                transfer_attempted=False,
                transfer_successful=False,
                response_message=(
                    "Lo siento, no tenemos contactos de emergencia configurados. "
                    "Por favor diríjase a la clínica más cercana."
                ),
            )

        # Sort by priority
        sorted_contacts = sorted(contacts, key=lambda x: x.get("priority", 99))

        # For critical emergencies, try to transfer the call
        transfer_attempted = False
        transfer_successful = False

        if channel == "voice" and urgency_level in ["critical", "high"]:
            # Get on-call vet
            on_call = next(
                (c for c in sorted_contacts if c.get("role") == "veterinarian"),
                sorted_contacts[0] if sorted_contacts else None,
            )

            if on_call:
                transfer_attempted = True
                # The actual transfer is handled by TwiML in the voice webhook
                # Here we just prepare the response

        # Send alerts to all relevant contacts
        alert_results = await self.notifications.send_emergency_alert(
            clinic=clinic,
            caller_phone=caller_phone,
            symptoms=symptoms,
            urgency_level=urgency_level,
        )

        # Generate response message
        response = await self._generate_emergency_response(
            urgency_level=urgency_level,
            symptoms=symptoms,
            transfer_attempted=transfer_attempted,
            channel=channel,
        )

        return EscalationResult(
            success=any(r["success"] for r in alert_results),
            action_taken="escalated",
            contacts_notified=alert_results,
            transfer_attempted=transfer_attempted,
            transfer_successful=transfer_successful,
            response_message=response,
        )

    async def _generate_emergency_response(
        self,
        urgency_level: str,
        symptoms: list[str],
        transfer_attempted: bool,
        channel: str,
    ) -> str:
        """Generate appropriate emergency response message."""
        if transfer_attempted:
            return (
                "Entiendo su preocupación. Esta situación requiere atención urgente. "
                "Voy a transferir su llamada con el veterinario de turno. "
                "Por favor no cuelgue."
            )

        if urgency_level == "critical":
            return (
                "Esta es una emergencia crítica. He enviado una alerta al equipo veterinario. "
                "Le contactarán en los próximos minutos. "
                "Mientras tanto, mantenga a su mascota tranquila y no intente darle comida o agua."
            )

        if urgency_level == "high":
            return (
                "Esta situación requiere atención veterinaria pronto. "
                "He notificado al equipo y le contactarán en breve. "
                "¿Necesita instrucciones mientras espera?"
            )

        return (
            "He tomado nota de los síntomas. Le recomiendo traer a su mascota "
            "a la clínica hoy si es posible. ¿Desea que le agende una cita prioritaria?"
        )

    async def get_first_aid_instructions(
        self, symptoms: list[str]
    ) -> Optional[str]:
        """Get first aid instructions for symptoms."""
        from app.prompts.emergency import FIRST_AID_TIPS

        instructions = []

        symptom_keywords = {
            "bleeding": ["sangre", "sangrado", "hemorragia"],
            "seizure": ["convulsión", "convulsiones", "temblor", "temblores"],
            "heat_stroke": ["calor", "golpe de calor", "jadeo excesivo"],
            "poisoning": ["veneno", "tóxico", "envenenamiento", "comió algo"],
            "choking": ["ahogando", "atragantado", "no puede respirar"],
        }

        symptoms_lower = [s.lower() for s in symptoms]

        for tip_key, keywords in symptom_keywords.items():
            if any(kw in " ".join(symptoms_lower) for kw in keywords):
                if tip_key in FIRST_AID_TIPS:
                    instructions.append(FIRST_AID_TIPS[tip_key])

        if instructions:
            return " ".join(instructions)

        return None

    def get_transfer_number(self, clinic: Clinic) -> Optional[str]:
        """Get the number to transfer emergency calls to."""
        contacts = clinic.escalation_contacts or []

        # First try on-call vet
        on_call = next(
            (c for c in contacts if c.get("is_on_call") or c.get("role") == "veterinarian"),
            None,
        )

        if on_call:
            return on_call.get("phone")

        # Fall back to first contact
        if contacts:
            return contacts[0].get("phone")

        return None

    async def escalate_conversation(
        self,
        clinic: Clinic,
        conversation_id: UUID,
        reason: str,
    ) -> bool:
        """Escalate a conversation for human review."""
        return await self.notifications.send_escalation_notification(
            clinic=clinic,
            conversation_id=conversation_id,
            reason=reason,
        )
