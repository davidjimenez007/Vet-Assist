"""Follow-up processor - sends scheduled follow-up messages."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FollowUp, Client, Pet, Conversation, ConversationMessage
from app.services.whatsapp.sender import whatsapp_sender
from app.services.whatsapp.states import ConversationState

logger = logging.getLogger(__name__)


class FollowUpProcessor:
    """Processes and sends scheduled follow-up messages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_pending_follow_ups(self) -> dict:
        """
        Process all pending follow-ups that are due.
        Returns summary of processed follow-ups.
        """
        now = datetime.utcnow()

        # Get pending follow-ups that are due
        result = await self.db.execute(
            select(FollowUp)
            .where(
                FollowUp.status == "pending",
                FollowUp.scheduled_at <= now
            )
            .order_by(FollowUp.scheduled_at)
            .limit(50)  # Process in batches
        )
        follow_ups = result.scalars().all()

        sent = 0
        failed = 0

        for follow_up in follow_ups:
            try:
                success = await self._send_follow_up(follow_up)
                if success:
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                logger.exception(f"Error processing follow-up {follow_up.id}: {e}")
                follow_up.status = "failed"
                follow_up.error_message = str(e)
                failed += 1

        await self.db.commit()

        return {
            "processed": len(follow_ups),
            "sent": sent,
            "failed": failed
        }

    async def _send_follow_up(self, follow_up: FollowUp) -> bool:
        """Send a single follow-up message."""
        # Get client
        client = await self.db.get(Client, follow_up.client_id)
        if not client:
            follow_up.status = "failed"
            follow_up.error_message = "Client not found"
            return False

        # Format message with pet name if available
        message = follow_up.message_template
        if follow_up.pet_id:
            pet = await self.db.get(Pet, follow_up.pet_id)
            if pet and pet.name:
                message = message.replace("{pet_name}", pet.name)
        message = message.replace("{pet_name}", "tu mascota")

        # Create conversation for the follow-up
        conversation = Conversation(
            clinic_id=follow_up.clinic_id,
            client_id=client.id,
            client_phone=client.phone,
            channel="whatsapp",
            conversation_type="follow_up",
            state=ConversationState.COLLECT_STATUS.value,
            status="active"
        )
        self.db.add(conversation)
        await self.db.flush()

        # Update follow-up with conversation
        follow_up.conversation_id = conversation.id

        # Save outgoing message
        outgoing = ConversationMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=message
        )
        self.db.add(outgoing)

        # Send via WhatsApp
        result = await whatsapp_sender.send(client.phone, message)

        if result.get("status") == "sent":
            follow_up.status = "sent"
            follow_up.sent_at = datetime.utcnow()
            logger.info(f"Follow-up {follow_up.id} sent to {client.phone}")
            return True
        else:
            follow_up.status = "failed"
            follow_up.error_message = result.get("message", "Unknown error")
            logger.error(f"Follow-up {follow_up.id} failed: {follow_up.error_message}")
            return False


async def process_follow_ups(db: AsyncSession) -> dict:
    """Helper function to process follow-ups."""
    processor = FollowUpProcessor(db)
    return await processor.process_pending_follow_ups()


# Default follow-up protocols
DEFAULT_PROTOCOLS = {
    "surgery": {
        "name": "Post-cirugía",
        "schedule_hours": [24, 48, 72, 168],
        "message_templates": [
            "Hola, ¿cómo sigue {pet_name} después de la cirugía de ayer? ¿Ha comido y orinado con normalidad?",
            "Hola, segundo día post-operatorio. ¿Cómo va la recuperación de {pet_name}? ¿Alguna molestia o sangrado?",
            "Hola, ¿cómo sigue {pet_name}? ¿La herida se ve bien? ¿Ha tenido fiebre o dejado de comer?",
            "Hola, esta semana toca revisión de puntos para {pet_name}. ¿Quieres que agendemos la cita?"
        ],
        "escalation_keywords": ["sangre", "sangrado", "fiebre", "no come", "hinchado", "pus", "olor", "vomita"]
    },
    "vaccination": {
        "name": "Post-vacuna",
        "schedule_hours": [24],
        "message_templates": [
            "Hola, ¿cómo está {pet_name} después de la vacuna? Es normal algo de decaimiento. Si presenta vómito, diarrea o hinchazón en la cara, escríbenos de inmediato."
        ],
        "escalation_keywords": ["vómito", "diarrea", "hinchazón", "cara hinchada", "no respira", "temblando"]
    },
    "consultation": {
        "name": "Post-consulta",
        "schedule_hours": [48],
        "message_templates": [
            "Hola, ¿cómo sigue {pet_name}? ¿Ha mejorado con el tratamiento?"
        ],
        "escalation_keywords": ["peor", "empeora", "no mejora", "igual", "mal"]
    },
    "dental": {
        "name": "Post-limpieza dental",
        "schedule_hours": [24, 72],
        "message_templates": [
            "Hola, ¿cómo está {pet_name} después de la limpieza dental? Recuerda que no debe comer alimento duro por 24 horas.",
            "Hola, ¿cómo va {pet_name}? ¿Ya puede comer con normalidad? ¿Alguna molestia?"
        ],
        "escalation_keywords": ["sangre", "no come", "dolor", "hinchado"]
    }
}
