"""Orchestrator for coordinating conversation agents."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clinic
from app.services.conversation import ConversationService
from app.services.calendar import CalendarService
from app.services.ai import AIService
from app.services.notification import NotificationService
from app.agents.intent_agent import IntentAgent, Intent, IntentResult
from app.agents.scheduling_agent import SchedulingAgent, SchedulingState
from app.agents.escalation_agent import EscalationAgent
from app.agents.voice_agent import VoiceAgent


@dataclass
class OrchestratorResponse:
    """Response from the orchestrator."""

    message: str
    twiml: Optional[str] = None
    end_conversation: bool = False
    appointment_booked: bool = False
    escalated: bool = False


class Orchestrator:
    """Main orchestrator for conversation handling."""

    def __init__(self, db: AsyncSession, clinic: Clinic):
        self.db = db
        self.clinic = clinic

        # Initialize services
        self.conversation_service = ConversationService(db)
        self.calendar_service = CalendarService(db)
        self.ai_service = AIService()
        self.notification_service = NotificationService()

        # Initialize agents
        self.intent_agent = IntentAgent(self.ai_service)
        self.scheduling_agent = SchedulingAgent(self.calendar_service, self.ai_service)
        self.escalation_agent = EscalationAgent(self.notification_service)
        self.voice_agent = VoiceAgent()

    async def handle_voice_incoming(
        self, call_sid: str, caller_phone: str
    ) -> str:
        """Handle incoming voice call."""
        # Create conversation
        conversation = await self.conversation_service.create_conversation(
            clinic_id=self.clinic.id,
            channel="voice",
            external_id=call_sid,
            client_phone=caller_phone,
        )

        # Generate greeting TwiML
        gather_action = f"/webhooks/voice/gather?conversation_id={conversation.id}"

        return self.voice_agent.create_greeting(
            clinic_name=self.clinic.name,
            gather_action=gather_action,
        )

    async def handle_voice_input(
        self,
        conversation_id: UUID,
        speech_result: str,
        caller_phone: str,
    ) -> str:
        """Handle voice input from user."""
        # Get conversation state
        state = await self.conversation_service.get_conversation_state(conversation_id)

        # Add user message
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=speech_result,
        )

        # Process based on current state
        response = await self._process_input(
            state=state,
            message=speech_result,
            caller_phone=caller_phone,
            channel="voice",
        )

        # Add assistant message
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.message,
        )

        # Generate TwiML
        if response.end_conversation:
            return self.voice_agent.create_goodbye(booked=response.appointment_booked)
        elif response.escalated:
            transfer_number = self.escalation_agent.get_transfer_number(self.clinic)
            if transfer_number:
                return self.voice_agent.create_transfer(transfer_number)
            else:
                return self.voice_agent.create_response(
                    message=response.message,
                    end_call=True,
                )
        else:
            gather_action = f"/webhooks/voice/gather?conversation_id={conversation_id}"
            return self.voice_agent.create_response(
                message=response.message,
                gather_action=gather_action,
            )

    async def handle_whatsapp_message(
        self,
        message_sid: str,
        sender_phone: str,
        message_body: str,
    ) -> str:
        """Handle incoming WhatsApp message."""
        # Find or create conversation
        conversation = await self.conversation_service.get_active_conversation(
            clinic_id=self.clinic.id,
            client_phone=sender_phone,
            channel="whatsapp",
        )

        if not conversation:
            conversation = await self.conversation_service.create_conversation(
                clinic_id=self.clinic.id,
                channel="whatsapp",
                external_id=message_sid,
                client_phone=sender_phone,
            )

        # Get conversation state
        state = await self.conversation_service.get_conversation_state(conversation.id)

        # Add user message
        await self.conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content=message_body,
        )

        # Process input
        response = await self._process_input(
            state=state,
            message=message_body,
            caller_phone=sender_phone,
            channel="whatsapp",
        )

        # Add assistant message
        await self.conversation_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response.message,
        )

        if response.end_conversation:
            await self.conversation_service.end_conversation(
                conversation_id=conversation.id,
                outcome="appointment_scheduled" if response.appointment_booked else "completed",
            )

        return response.message

    async def _process_input(
        self,
        state,
        message: str,
        caller_phone: str,
        channel: str,
    ) -> OrchestratorResponse:
        """Process user input and generate response."""
        current_state = state.current_state
        collected_data = state.collected_data

        # Get conversation history for context
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in state.messages[-10:]  # Last 10 messages
        ]

        # Detect intent if in early states
        if current_state in ["greeting", "intent_detection"]:
            intent_result = await self.intent_agent.detect(message, history)

            if intent_result.is_emergency:
                # Handle emergency
                return await self._handle_emergency(
                    state=state,
                    intent_result=intent_result,
                    caller_phone=caller_phone,
                    channel=channel,
                )

            # Update state based on intent
            await self.conversation_service.update_state(
                conversation_id=state.id,
                new_state=self._get_next_state(intent_result.intent),
                intent=intent_result.intent.value,
                collected_data=intent_result.extracted_data,
            )

            if intent_result.intent == Intent.SCHEDULE:
                return await self._handle_scheduling(
                    state=state,
                    message=message,
                    caller_phone=caller_phone,
                    channel=channel,
                )
            elif intent_result.intent == Intent.QUESTION:
                return await self._handle_question(message, channel)
            else:
                return OrchestratorResponse(
                    message=await self.ai_service.generate_clarification([], channel),
                )

        elif current_state in ["schedule", "collect_info", "propose_slots", "confirm_booking"]:
            return await self._handle_scheduling(
                state=state,
                message=message,
                caller_phone=caller_phone,
                channel=channel,
            )

        elif current_state in ["emergency", "triage", "escalate"]:
            return await self._handle_emergency_followup(
                state=state,
                message=message,
                caller_phone=caller_phone,
                channel=channel,
            )

        else:
            # Default: try to understand what user wants
            return OrchestratorResponse(
                message="¿En qué puedo ayudarle?",
            )

    async def _handle_scheduling(
        self,
        state,
        message: str,
        caller_phone: str,
        channel: str,
    ) -> OrchestratorResponse:
        """Handle scheduling flow with conversation context."""
        # Build scheduling state from collected data
        scheduling_state = SchedulingState.from_dict(state.collected_data)
        scheduling_state.client_phone = caller_phone

        # Get conversation history for context
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in state.messages[-10:]  # Last 10 messages for context
        ]

        # Process message with conversation context
        new_state, response, ready_to_book = await self.scheduling_agent.process_message(
            message=message,
            state=scheduling_state,
            clinic_id=state.clinic_id,
            conversation_history=history,
            channel=channel,
        )

        # Update conversation state
        await self.conversation_service.update_state(
            conversation_id=state.id,
            new_state="confirm_booking" if ready_to_book else "collect_info",
            collected_data=new_state.to_dict(),
        )

        if ready_to_book:
            # Book the appointment
            result = await self.scheduling_agent.book(
                state=new_state,
                clinic_id=state.clinic_id,
                conversation_id=state.id,
            )

            if result.success:
                await self.conversation_service.end_conversation(
                    conversation_id=state.id,
                    outcome="appointment_scheduled",
                )

                return OrchestratorResponse(
                    message=result.confirmation_message,
                    end_conversation=True,
                    appointment_booked=True,
                )
            else:
                return OrchestratorResponse(
                    message=f"Lo siento, {result.error}. ¿Desea intentar con otro horario?",
                )

        return OrchestratorResponse(message=response)

    async def _handle_emergency(
        self,
        state,
        intent_result: IntentResult,
        caller_phone: str,
        channel: str,
    ) -> OrchestratorResponse:
        """Handle emergency situation."""
        await self.conversation_service.update_state(
            conversation_id=state.id,
            new_state="emergency",
            intent="EMERGENCY",
            collected_data={"symptoms": intent_result.symptoms},
        )

        # Escalate
        result = await self.escalation_agent.handle_emergency(
            clinic=self.clinic,
            caller_phone=caller_phone,
            urgency_level=intent_result.urgency_level,
            symptoms=intent_result.symptoms,
            channel=channel,
        )

        await self.conversation_service.end_conversation(
            conversation_id=state.id,
            outcome="escalated",
            status="escalated",
        )

        return OrchestratorResponse(
            message=result.response_message,
            escalated=True,
            end_conversation=not result.transfer_attempted,
        )

    async def _handle_emergency_followup(
        self,
        state,
        message: str,
        caller_phone: str,
        channel: str,
    ) -> OrchestratorResponse:
        """Handle follow-up in emergency conversation."""
        # Get any first aid instructions
        symptoms = state.collected_data.get("symptoms", [])
        instructions = await self.escalation_agent.get_first_aid_instructions(symptoms)

        if instructions:
            return OrchestratorResponse(
                message=f"Mientras espera, {instructions}",
            )

        return OrchestratorResponse(
            message="El equipo veterinario ha sido notificado y le contactarán pronto.",
            end_conversation=True,
        )

    async def _handle_question(
        self, message: str, channel: str
    ) -> OrchestratorResponse:
        """Handle general question."""
        clinic_info = {
            "name": self.clinic.name,
            "working_hours": self.clinic.working_hours,
        }

        answer = await self.ai_service.answer_question(message, clinic_info)

        return OrchestratorResponse(
            message=answer,
            end_conversation=False,
        )

    def _get_next_state(self, intent: Intent) -> str:
        """Get the next conversation state based on intent."""
        state_map = {
            Intent.SCHEDULE: "collect_info",
            Intent.EMERGENCY: "emergency",
            Intent.QUESTION: "answer",
            Intent.UNCLEAR: "clarify",
        }
        return state_map.get(intent, "greeting")
