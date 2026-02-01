"""Notification service for SMS and WhatsApp alerts."""

from typing import Optional
from uuid import UUID

from app.services.twilio_client import TwilioService
from app.models import Clinic, Appointment


class NotificationService:
    """Service for sending notifications via SMS and WhatsApp."""

    def __init__(self, twilio_service: Optional[TwilioService] = None):
        self.twilio = twilio_service or TwilioService()

    async def send_appointment_confirmation(
        self,
        phone: str,
        appointment: Appointment,
        clinic: Clinic,
        channel: str = "sms",
    ) -> bool:
        """Send appointment confirmation to client."""
        import pytz

        tz = pytz.timezone(clinic.timezone)
        local_time = appointment.start_time.astimezone(tz)

        message = (
            f"Cita confirmada en {clinic.name}\n"
            f"Fecha: {local_time.strftime('%d/%m/%Y')}\n"
            f"Hora: {local_time.strftime('%I:%M %p')}\n"
            f"Tipo: {appointment.appointment_type}\n\n"
            "Te esperamos."
        )

        if channel == "whatsapp":
            return await self.twilio.send_whatsapp(phone, message)
        else:
            return await self.twilio.send_sms(phone, message)

    async def send_appointment_reminder(
        self,
        phone: str,
        appointment: Appointment,
        clinic: Clinic,
    ) -> bool:
        """Send appointment reminder (typically 24h before)."""
        import pytz

        tz = pytz.timezone(clinic.timezone)
        local_time = appointment.start_time.astimezone(tz)

        message = (
            f"Recordatorio: tienes cita mañana en {clinic.name}\n"
            f"Hora: {local_time.strftime('%I:%M %p')}\n\n"
            "¿Confirmas tu asistencia? Responde SI o NO."
        )

        return await self.twilio.send_sms(phone, message)

    async def send_emergency_alert(
        self,
        clinic: Clinic,
        caller_phone: str,
        symptoms: list[str],
        urgency_level: str,
    ) -> list[dict]:
        """Send emergency alerts to escalation contacts."""
        results = []
        contacts = clinic.escalation_contacts or []

        # Sort by priority
        sorted_contacts = sorted(contacts, key=lambda x: x.get("priority", 99))

        for contact in sorted_contacts:
            message = (
                f"🚨 EMERGENCIA en {clinic.name}\n\n"
                f"Llamada de: {caller_phone}\n"
                f"Urgencia: {urgency_level.upper()}\n"
                f"Síntomas: {', '.join(symptoms) if symptoms else 'No especificados'}\n\n"
                "Por favor contactar al cliente inmediatamente."
            )

            contact_phone = contact.get("phone")
            if not contact_phone:
                continue

            # Try WhatsApp first, then SMS
            success = await self.twilio.send_whatsapp(contact_phone, message)
            if not success:
                success = await self.twilio.send_sms(contact_phone, message)

            results.append({
                "contact": contact.get("name"),
                "phone": contact_phone,
                "success": success,
            })

            # Stop after first successful contact for high urgency
            if success and urgency_level in ["high", "critical"]:
                break

        return results

    async def send_escalation_notification(
        self,
        clinic: Clinic,
        conversation_id: UUID,
        reason: str,
    ) -> bool:
        """Send notification about escalated conversation."""
        contacts = clinic.escalation_contacts or []

        if not contacts:
            return False

        # Get first admin contact
        admin_contact = next(
            (c for c in contacts if c.get("role") == "admin"),
            contacts[0] if contacts else None,
        )

        if not admin_contact:
            return False

        message = (
            f"Conversación escalada en {clinic.name}\n"
            f"ID: {conversation_id}\n"
            f"Razón: {reason}\n\n"
            "Por favor revisar en el dashboard."
        )

        return await self.twilio.send_sms(admin_contact.get("phone"), message)

    async def send_sms(self, phone: str, message: str) -> bool:
        """Send a generic SMS message."""
        return await self.twilio.send_sms(phone, message)

    async def send_whatsapp(self, phone: str, message: str) -> bool:
        """Send a generic WhatsApp message."""
        return await self.twilio.send_whatsapp(phone, message)
