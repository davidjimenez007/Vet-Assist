"""Conversation engine - main orchestrator for WhatsApp conversations."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Clinic, Client, Conversation, ConversationMessage,
    Appointment, EmergencyEvent, EmergencyAlert
)
from app.services.whatsapp.states import (
    ConversationState, get_timeout_duration, can_transition, is_terminal_state
)
from app.services.whatsapp.intent import IntentClassifier, Intent
from app.services.whatsapp.sender import whatsapp_sender

logger = logging.getLogger(__name__)


class ConversationEngine:
    """Main engine for processing WhatsApp conversations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.intent_classifier = IntentClassifier()

    async def process_incoming_message(
        self,
        clinic_id: uuid.UUID,
        phone: str,
        message_text: str,
        external_id: Optional[str] = None
    ) -> dict:
        """
        Process an incoming WhatsApp message.

        Args:
            clinic_id: Clinic UUID
            phone: Client phone number
            message_text: Message content
            external_id: Twilio message SID

        Returns:
            dict with response and conversation info
        """
        # Get or create conversation
        conversation = await self._get_or_create_conversation(
            clinic_id, phone, external_id
        )

        # Save incoming message
        await self._save_message(conversation.id, "user", message_text)

        # Get clinic for context
        clinic = await self._get_clinic(clinic_id)

        # Process based on current state
        response = await self._process_state(
            conversation, message_text, clinic
        )

        # Save response message
        if response.get("message"):
            await self._save_message(conversation.id, "assistant", response["message"])

        # Send response via WhatsApp
        if response.get("message") and response.get("send", True):
            await whatsapp_sender.send(phone, response["message"])

        await self.db.commit()

        return {
            "conversation_id": str(conversation.id),
            "state": conversation.state,
            "response": response.get("message"),
            "action": response.get("action"),
            "data": response.get("data", {})
        }

    async def _get_or_create_conversation(
        self,
        clinic_id: uuid.UUID,
        phone: str,
        external_id: Optional[str] = None
    ) -> Conversation:
        """Get active conversation or create new one."""
        # Look for active conversation with this phone
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.clinic_id == clinic_id,
                Conversation.client_phone == phone,
                Conversation.status == "active"
            )
            .order_by(Conversation.started_at.desc())
            .limit(1)
        )
        conversation = result.scalar_one_or_none()

        if conversation:
            # Check if conversation timed out
            if conversation.timeout_at and datetime.utcnow() > conversation.timeout_at:
                # Close old conversation
                conversation.status = "abandoned"
                conversation.state = ConversationState.CLOSED.value
                conversation.ended_at = datetime.utcnow()
                conversation = None

        if not conversation:
            # Get or create client
            client = await self._get_or_create_client(clinic_id, phone)

            # Create new conversation
            conversation = Conversation(
                clinic_id=clinic_id,
                client_id=client.id if client else None,
                client_phone=phone,
                channel="whatsapp",
                external_id=external_id,
                conversation_type="inbound",
                state=ConversationState.GREETING.value,
                status="active",
                started_at=datetime.utcnow()
            )
            self.db.add(conversation)
            await self.db.flush()

        # Update timeout
        timeout = get_timeout_duration(ConversationState(conversation.state))
        if timeout:
            conversation.timeout_at = datetime.utcnow() + timeout

        return conversation

    async def _get_or_create_client(
        self,
        clinic_id: uuid.UUID,
        phone: str
    ) -> Optional[Client]:
        """Get or create client by phone."""
        result = await self.db.execute(
            select(Client)
            .where(
                Client.clinic_id == clinic_id,
                Client.phone == phone
            )
        )
        client = result.scalar_one_or_none()

        if not client:
            client = Client(
                clinic_id=clinic_id,
                phone=phone
            )
            self.db.add(client)
            await self.db.flush()

        return client

    async def _get_clinic(self, clinic_id: uuid.UUID) -> Optional[Clinic]:
        """Get clinic by ID."""
        result = await self.db.execute(
            select(Clinic).where(Clinic.id == clinic_id)
        )
        return result.scalar_one_or_none()

    async def _save_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str
    ) -> ConversationMessage:
        """Save a message to the conversation."""
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def _process_state(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Process message based on current conversation state."""
        state = ConversationState(conversation.state)
        clinic_name = clinic.name if clinic else "la clínica"

        # State handlers
        handlers = {
            ConversationState.GREETING: self._handle_greeting,
            ConversationState.INTENT_DETECTION: self._handle_intent_detection,
            ConversationState.ASK_REASON: self._handle_ask_reason,
            ConversationState.OFFER_SLOTS: self._handle_offer_slots,
            ConversationState.AWAIT_SELECTION: self._handle_await_selection,
            ConversationState.CONFIRM_BOOKING: self._handle_confirm_booking,
            ConversationState.CONFIRM_EMERGENCY: self._handle_confirm_emergency,
            ConversationState.ESCALATE: self._handle_escalate,
            ConversationState.COLLECT_STATUS: self._handle_collect_status,
            ConversationState.REMINDER: self._handle_reminder,
            ConversationState.COMPLETED: self._handle_completed,
            ConversationState.CLOSED: self._handle_closed,
        }

        handler = handlers.get(state, self._handle_unknown)
        return await handler(conversation, message, clinic)

    async def _transition_state(
        self,
        conversation: Conversation,
        new_state: ConversationState
    ):
        """Transition conversation to a new state."""
        current = ConversationState(conversation.state)

        if not can_transition(current, new_state):
            logger.warning(
                f"Invalid state transition: {current} -> {new_state}"
            )
            return

        conversation.state = new_state.value
        conversation.last_state_change = datetime.utcnow()

        # Set new timeout
        timeout = get_timeout_duration(new_state)
        if timeout:
            conversation.timeout_at = datetime.utcnow() + timeout
        else:
            conversation.timeout_at = None

        # If terminal state, close conversation
        if is_terminal_state(new_state):
            conversation.status = "completed"
            conversation.ended_at = datetime.utcnow()

    # ===========================================
    # State Handlers
    # ===========================================

    async def _handle_greeting(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle GREETING state - initial contact."""
        clinic_name = clinic.name if clinic else "la clínica"

        # Classify intent from first message
        intent_result = self.intent_classifier.classify(message)

        # Check for emergency immediately
        if intent_result.is_emergency_potential:
            conversation.emergency_keywords = intent_result.emergency_keywords
            conversation.emergency_description = message
            await self._transition_state(conversation, ConversationState.CONFIRM_EMERGENCY)
            return {
                "message": (
                    "Entiendo que puede ser una emergencia.\n"
                    "Para confirmar: ¿la vida de tu mascota está en riesgo en este momento?\n\n"
                    "Responde SÍ o NO"
                ),
                "action": "emergency_confirm"
            }

        # Check for scheduling intent
        if intent_result.intent == Intent.SCHEDULING:
            await self._transition_state(conversation, ConversationState.ASK_REASON)
            return {
                "message": (
                    f"Hola, bienvenido a {clinic_name}. Con gusto te ayudo a agendar una cita.\n\n"
                    "¿Cuál es el motivo de la consulta?"
                ),
                "action": "ask_reason"
            }

        # Default greeting response
        await self._transition_state(conversation, ConversationState.INTENT_DETECTION)
        return {
            "message": (
                f"Hola, bienvenido a {clinic_name}. Soy el asistente virtual.\n\n"
                "¿En qué puedo ayudarte hoy?\n"
                "• Agendar una cita\n"
                "• Consultar horarios\n"
                "• Reportar una emergencia"
            ),
            "action": "greeting"
        }

    async def _handle_intent_detection(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle INTENT_DETECTION state - determine what user wants."""
        intent_result = self.intent_classifier.classify(message)

        # Emergency
        if intent_result.is_emergency_potential:
            conversation.emergency_keywords = intent_result.emergency_keywords
            conversation.emergency_description = message
            await self._transition_state(conversation, ConversationState.CONFIRM_EMERGENCY)
            return {
                "message": (
                    "Entiendo que puede ser una emergencia.\n"
                    "Para confirmar: ¿la vida de tu mascota está en riesgo en este momento?\n\n"
                    "Responde SÍ o NO"
                ),
                "action": "emergency_confirm"
            }

        # Scheduling
        if intent_result.intent == Intent.SCHEDULING:
            await self._transition_state(conversation, ConversationState.ASK_REASON)
            return {
                "message": "Con gusto te ayudo a agendar. ¿Cuál es el motivo de la consulta?",
                "action": "ask_reason"
            }

        # Unclear - prompt for scheduling
        return {
            "message": (
                "No estoy seguro de entender. ¿Te gustaría agendar una cita?\n\n"
                "Escribe 'sí' para agendar o describe qué necesitas."
            ),
            "action": "clarify"
        }

    async def _handle_ask_reason(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle ASK_REASON state - collect consultation reason."""
        # Check for emergency in reason
        intent_result = self.intent_classifier.classify(message)
        if intent_result.is_emergency_potential:
            conversation.emergency_keywords = intent_result.emergency_keywords
            conversation.emergency_description = message
            await self._transition_state(conversation, ConversationState.CONFIRM_EMERGENCY)
            return {
                "message": (
                    "Parece que puede ser urgente.\n"
                    "Para confirmar: ¿la vida de tu mascota está en riesgo en este momento?\n\n"
                    "Responde SÍ o NO"
                ),
                "action": "emergency_confirm"
            }

        # Save reason and get available slots
        conversation.extracted_reason = message

        # Get available slots for next 3 days
        slots = await self._get_available_slots(conversation.clinic_id, clinic)

        if not slots:
            return {
                "message": (
                    "Lo siento, no hay disponibilidad en los próximos días.\n"
                    "Por favor llama directamente a la clínica para agendar."
                ),
                "action": "no_slots"
            }

        # Store offered slots
        conversation.offered_slots = {
            "slots": [
                {"index": i, "start": s["start"].isoformat(), "display": s["display"]}
                for i, s in enumerate(slots[:3])
            ]
        }

        # Format slot options
        slot_text = "\n".join([
            f"{i+1}. {s['display']}" for i, s in enumerate(slots[:3])
        ])

        await self._transition_state(conversation, ConversationState.OFFER_SLOTS)
        return {
            "message": (
                f"Entendido: {message[:50]}{'...' if len(message) > 50 else ''}\n\n"
                f"Tengo disponibilidad:\n\n{slot_text}\n\n"
                "¿Cuál te funciona mejor? (responde 1, 2 o 3)"
            ),
            "action": "offer_slots"
        }

    async def _handle_offer_slots(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle OFFER_SLOTS state - wait for slot selection."""
        return await self._handle_await_selection(conversation, message, clinic)

    async def _handle_await_selection(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle AWAIT_SELECTION state - parse slot choice."""
        offered = conversation.offered_slots.get("slots", [])
        num_options = len(offered)

        # Try to parse selection
        selection = self.intent_classifier.parse_slot_selection(message, num_options)

        if selection is not None and selection < len(offered):
            selected_slot = offered[selection]
            conversation.state_data = {
                "selected_slot": selected_slot
            }

            await self._transition_state(conversation, ConversationState.CONFIRM_BOOKING)

            # Format confirmation
            reason = conversation.extracted_reason or "Consulta"
            return {
                "message": (
                    f"Perfecto. Confirmo tu cita:\n\n"
                    f"📅 {selected_slot['display']}\n"
                    f"📋 {reason[:50]}\n\n"
                    "¿Confirmas esta cita? (Sí/No)"
                ),
                "action": "confirm_booking"
            }

        # Could not parse - ask again
        slot_text = "\n".join([
            f"{i+1}. {s['display']}" for i, s in enumerate(offered)
        ])
        return {
            "message": (
                f"No entendí tu selección. Por favor responde con el número:\n\n"
                f"{slot_text}\n\n"
                "¿Cuál prefieres? (1, 2 o 3)"
            ),
            "action": "ask_selection_again"
        }

    async def _handle_confirm_booking(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle CONFIRM_BOOKING state - final confirmation."""
        intent_result = self.intent_classifier.classify(message)

        if intent_result.intent == Intent.CONFIRMATION:
            # Create appointment
            selected = conversation.state_data.get("selected_slot", {})
            appointment = await self._create_appointment(
                conversation, selected, clinic
            )

            await self._transition_state(conversation, ConversationState.COMPLETED)

            return {
                "message": (
                    "✓ Cita confirmada.\n\n"
                    f"📅 {selected.get('display', '')}\n\n"
                    "Te esperamos. Si necesitas cancelar o cambiar, escríbenos con tiempo."
                ),
                "action": "booking_complete",
                "data": {"appointment_id": str(appointment.id) if appointment else None}
            }

        if intent_result.intent == Intent.REJECTION:
            # Go back to offer slots
            await self._transition_state(conversation, ConversationState.OFFER_SLOTS)
            offered = conversation.offered_slots.get("slots", [])
            slot_text = "\n".join([
                f"{i+1}. {s['display']}" for i, s in enumerate(offered)
            ])
            return {
                "message": (
                    f"Entendido. Estas son las opciones disponibles:\n\n"
                    f"{slot_text}\n\n"
                    "¿Cuál te funciona mejor?"
                ),
                "action": "offer_slots_again"
            }

        # Unclear response
        return {
            "message": "Por favor responde Sí para confirmar o No para ver otras opciones.",
            "action": "ask_confirm_again"
        }

    async def _handle_confirm_emergency(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle CONFIRM_EMERGENCY state - verify emergency."""
        intent_result = self.intent_classifier.classify(message)

        if intent_result.intent == Intent.CONFIRMATION:
            # Check for abuse
            client = await self._get_client_by_phone(
                conversation.clinic_id, conversation.client_phone
            )
            if client and client.emergency_access_revoked:
                await self._transition_state(conversation, ConversationState.CLOSED)
                return {
                    "message": (
                        "Lo siento, el acceso a emergencias está restringido.\n"
                        "Por favor llama directamente a la clínica."
                    ),
                    "action": "emergency_denied"
                }

            # Create emergency
            emergency = await self._create_emergency(conversation, clinic)
            await self._transition_state(conversation, ConversationState.ESCALATE)

            return {
                "message": (
                    "🚨 EMERGENCIA REGISTRADA\n\n"
                    "El veterinario ha sido notificado y te contactará en los próximos minutos.\n\n"
                    "Mientras tanto:\n"
                    "• Mantén a tu mascota tranquila\n"
                    "• No le des medicamentos sin indicación\n"
                    "• Ten a la mano cualquier información relevante\n\n"
                    "¿En qué dirección te encuentras?"
                ),
                "action": "emergency_escalated",
                "data": {"emergency_id": str(emergency.id) if emergency else None}
            }

        if intent_result.intent == Intent.REJECTION:
            # Not a real emergency - redirect to scheduling
            if conversation.client_id:
                client = await self.db.get(Client, conversation.client_id)
                if client:
                    client.false_emergency_count += 1

            await self._transition_state(conversation, ConversationState.ASK_REASON)
            return {
                "message": (
                    "Entendido, no es una emergencia.\n\n"
                    "¿Te gustaría agendar una cita regular? "
                    "Cuéntame el motivo de la consulta."
                ),
                "action": "redirect_to_scheduling"
            }

        # Unclear
        return {
            "message": (
                "Por favor responde SÍ si es una emergencia real, "
                "o NO si no lo es."
            ),
            "action": "ask_emergency_again"
        }

    async def _handle_escalate(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle ESCALATE state - emergency was escalated."""
        # In escalate state, just acknowledge and log
        await self._save_message(conversation.id, "user", f"[Durante emergencia] {message}")

        return {
            "message": (
                "Tu mensaje ha sido registrado. "
                "El veterinario revisará toda la información."
            ),
            "action": "escalate_logged",
            "send": True
        }

    async def _handle_collect_status(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle COLLECT_STATUS state - follow-up response."""
        # Analyze response for concerning keywords
        concerning_keywords = [
            "sangre", "fiebre", "no come", "vomita", "peor",
            "hinchado", "pus", "olor", "no mejora"
        ]

        message_lower = message.lower()
        matched = [kw for kw in concerning_keywords if kw in message_lower]

        if matched:
            # Concerning response - notify vet
            await self._transition_state(conversation, ConversationState.COMPLETED)
            return {
                "message": (
                    "Gracias por la información. He notificado al veterinario "
                    "sobre estos síntomas para que los revise.\n\n"
                    "Te contactaremos pronto."
                ),
                "action": "followup_escalated",
                "data": {"concerning_keywords": matched}
            }

        # Normal response
        await self._transition_state(conversation, ConversationState.COMPLETED)
        return {
            "message": (
                "Gracias por la actualización. Nos alegra saber que va bien.\n\n"
                "Si notas cualquier cambio preocupante, escríbenos de inmediato."
            ),
            "action": "followup_complete"
        }

    async def _handle_reminder(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle REMINDER state - user resumed after reminder."""
        await self._transition_state(conversation, ConversationState.INTENT_DETECTION)
        return await self._handle_intent_detection(conversation, message, clinic)

    async def _handle_completed(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle COMPLETED state."""
        await self._transition_state(conversation, ConversationState.CLOSED)
        return {
            "message": "¿Hay algo más en lo que pueda ayudarte?",
            "action": "completed"
        }

    async def _handle_closed(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle CLOSED state - new conversation."""
        # Start new conversation
        await self._transition_state(conversation, ConversationState.GREETING)
        return await self._handle_greeting(conversation, message, clinic)

    async def _handle_unknown(
        self,
        conversation: Conversation,
        message: str,
        clinic: Clinic
    ) -> dict:
        """Handle unknown state."""
        logger.error(f"Unknown state: {conversation.state}")
        await self._transition_state(conversation, ConversationState.GREETING)
        return await self._handle_greeting(conversation, message, clinic)

    # ===========================================
    # Helper Methods
    # ===========================================

    async def _get_client_by_phone(
        self,
        clinic_id: uuid.UUID,
        phone: str
    ) -> Optional[Client]:
        """Get client by phone number."""
        result = await self.db.execute(
            select(Client)
            .where(
                Client.clinic_id == clinic_id,
                Client.phone == phone
            )
        )
        return result.scalar_one_or_none()

    async def _get_available_slots(
        self,
        clinic_id: uuid.UUID,
        clinic: Clinic,
        days_ahead: int = 3
    ) -> list[dict]:
        """Get available appointment slots."""
        from datetime import date, time

        slots = []
        today = date.today()

        for day_offset in range(days_ahead + 1):
            check_date = today + timedelta(days=day_offset)
            day_name = check_date.strftime("%A").lower()

            # Get working hours for this day
            hours = clinic.working_hours.get(day_name) if clinic else None
            if not hours:
                continue

            try:
                start_hour = int(hours["start"].split(":")[0])
                end_hour = int(hours["end"].split(":")[0])
            except (KeyError, ValueError):
                continue

            # Get existing appointments for this day
            result = await self.db.execute(
                select(Appointment)
                .where(
                    Appointment.clinic_id == clinic_id,
                    Appointment.start_time >= datetime.combine(check_date, time.min),
                    Appointment.start_time < datetime.combine(check_date, time.max),
                    Appointment.status.not_in(["cancelled"])
                )
            )
            existing = result.scalars().all()
            booked_hours = {apt.start_time.hour for apt in existing}

            # Generate available slots
            for hour in range(start_hour, end_hour):
                if hour in booked_hours:
                    continue

                slot_time = datetime.combine(check_date, time(hour=hour))

                # Skip past times for today
                if check_date == today and slot_time <= datetime.now():
                    continue

                # Format display
                day_display = {
                    0: "Lunes", 1: "Martes", 2: "Miércoles",
                    3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"
                }
                hour_display = f"{hour}:00"
                if hour < 12:
                    hour_display += " AM"
                elif hour == 12:
                    hour_display += " PM"
                else:
                    hour_display = f"{hour-12}:00 PM"

                date_str = check_date.strftime("%d/%m")
                if day_offset == 0:
                    display = f"Hoy {hour_display}"
                elif day_offset == 1:
                    display = f"Mañana {hour_display}"
                else:
                    display = f"{day_display[check_date.weekday()]} {date_str} {hour_display}"

                slots.append({
                    "start": slot_time,
                    "display": display
                })

                if len(slots) >= 5:
                    return slots

        return slots

    async def _create_appointment(
        self,
        conversation: Conversation,
        selected_slot: dict,
        clinic: Clinic
    ) -> Optional[Appointment]:
        """Create an appointment from conversation."""
        try:
            start_time = datetime.fromisoformat(selected_slot["start"])
        except (KeyError, ValueError):
            logger.error(f"Invalid slot data: {selected_slot}")
            return None

        duration = 30  # Default 30 minutes
        if clinic and clinic.appointment_duration_minutes:
            duration = clinic.appointment_duration_minutes.get("consultation", 30)

        appointment = Appointment(
            clinic_id=conversation.clinic_id,
            client_id=conversation.client_id,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration),
            duration_minutes=duration,
            appointment_type="consultation",
            reason=conversation.extracted_reason,
            status="scheduled",
            source="ai_whatsapp",
            conversation_id=conversation.id,
            priority="normal"
        )

        self.db.add(appointment)
        await self.db.flush()

        # Update conversation outcome
        conversation.outcome = "appointment_scheduled"

        return appointment

    async def _create_emergency(
        self,
        conversation: Conversation,
        clinic: Clinic
    ) -> Optional[EmergencyEvent]:
        """Create an emergency event and send alerts."""
        emergency = EmergencyEvent(
            clinic_id=conversation.clinic_id,
            conversation_id=conversation.id,
            client_id=conversation.client_id,
            client_phone=conversation.client_phone,
            pet_name=conversation.extracted_pet_name,
            pet_species=conversation.extracted_pet_species,
            description=conversation.emergency_description,
            keywords_detected=conversation.emergency_keywords or [],
            status="active",
            priority="high"
        )

        self.db.add(emergency)
        await self.db.flush()

        # Send alerts to escalation contacts
        if clinic and clinic.escalation_contacts:
            contacts = clinic.escalation_contacts
            if isinstance(contacts, list):
                for contact in contacts[:3]:  # Max 3 contacts
                    await self._send_emergency_alert(emergency, contact)

        # Update conversation
        conversation.outcome = "escalated"

        return emergency

    async def _send_emergency_alert(
        self,
        emergency: EmergencyEvent,
        contact: dict
    ) -> EmergencyAlert:
        """Send emergency alert to a contact."""
        phone = contact.get("phone", "")
        name = contact.get("name", "")
        role = contact.get("role", "")

        message = (
            f"🚨 EMERGENCIA\n\n"
            f"📞 {emergency.client_phone}\n"
            f"🐾 {emergency.pet_species or 'Mascota'}"
            f"{f' - {emergency.pet_name}' if emergency.pet_name else ''}\n"
            f"⚠️ {emergency.description[:100] if emergency.description else 'Sin descripción'}\n\n"
            f"Palabras clave: {', '.join(emergency.keywords_detected[:3])}"
        )

        alert = EmergencyAlert(
            emergency_id=emergency.id,
            contact_phone=phone,
            contact_name=name,
            contact_role=role,
            message_content=message,
            status="pending"
        )

        self.db.add(alert)
        await self.db.flush()

        # Send via WhatsApp
        if phone:
            result = await whatsapp_sender.send(phone, message)
            alert.status = "sent" if result.get("status") == "sent" else "failed"
            alert.sent_at = datetime.utcnow()
            if result.get("status") != "sent":
                alert.error_message = result.get("message")

        return alert
