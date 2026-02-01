"""Web chat endpoint for AI assistant."""

import logging
import re
from typing import Optional
from uuid import UUID

import openai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentClinic, CurrentUser, DBSession
from app.agents.orchestrator import Orchestrator, OrchestratorResponse
from app.services.conversation import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    """Incoming chat message."""
    message: str
    conversation_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    """Chat response."""
    message: str
    conversation_id: UUID
    end_conversation: bool = False
    appointment_booked: bool = False


def _fallback_response(message: str) -> OrchestratorResponse:
    """Generate a rule-based fallback when OpenAI is unavailable."""
    msg_lower = message.lower().strip()

    # Scheduling keywords
    schedule_words = ["cita", "agendar", "programar", "reservar", "turno", "consulta", "appointment"]
    if any(w in msg_lower for w in schedule_words):
        return OrchestratorResponse(
            message=(
                "Entiendo que quieres agendar una cita. En este momento el servicio de IA "
                "no esta disponible, pero puedes crear la cita directamente desde la seccion "
                "de Citas en el menu lateral. Si necesitas ayuda, contacta al equipo."
            ),
        )

    # Emergency keywords
    emergency_words = ["emergencia", "urgente", "sangre", "vomit", "convulsion", "envenen", "ahog"]
    if any(w in msg_lower for w in emergency_words):
        return OrchestratorResponse(
            message=(
                "Esto parece una emergencia. Por favor contacta directamente a la clinica "
                "por telefono. Si tu mascota esta en peligro inmediato, acude a la clinica "
                "veterinaria mas cercana de inmediato."
            ),
        )

    # Greeting
    greeting_words = ["hola", "buenos", "buenas", "hey", "hi"]
    if any(w in msg_lower for w in greeting_words):
        return OrchestratorResponse(
            message=(
                "Hola! El servicio de IA esta temporalmente limitado. "
                "Puedes usar el menu lateral para gestionar citas, clientes y mas. "
                "Cuando se resuelva la conexion con OpenAI, podre ayudarte con todo."
            ),
        )

    # Horario / schedule questions
    if "horario" in msg_lower or "hora" in msg_lower or "abren" in msg_lower:
        return OrchestratorResponse(
            message=(
                "Para ver los horarios de la clinica, ve a Configuracion en el menu lateral. "
                "Ahi puedes consultar y modificar los horarios de atencion."
            ),
        )

    # Default
    return OrchestratorResponse(
        message=(
            "El servicio de IA esta temporalmente limitado (la API key de OpenAI "
            "necesita creditos activos). Mientras tanto, puedes usar todas las "
            "funciones del panel: gestionar citas, clientes, mascotas y configuracion "
            "desde el menu lateral."
        ),
    )


@router.post("", response_model=ChatResponse)
async def send_chat_message(
    data: ChatMessage,
    current_user: CurrentUser,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Send a message to the AI assistant via web chat."""
    orchestrator = Orchestrator(db, current_clinic)

    try:
        if data.conversation_id:
            conversation = await orchestrator.conversation_service.get_conversation(
                data.conversation_id
            )
            if not conversation or conversation.status != "active":
                conversation = await orchestrator.conversation_service.create_conversation(
                    clinic_id=current_clinic.id,
                    channel="web",
                )
        else:
            conversation = await orchestrator.conversation_service.create_conversation(
                clinic_id=current_clinic.id,
                channel="web",
            )

            greeting = await orchestrator.ai_service.generate_greeting(
                current_clinic.name, "web"
            )
            await orchestrator.conversation_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=greeting,
            )

        # Get conversation state
        state = await orchestrator.conversation_service.get_conversation_state(
            conversation.id
        )

        # Add user message
        await orchestrator.conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content=data.message,
        )

        # Process through orchestrator, with fallback on OpenAI errors
        try:
            response = await orchestrator._process_input(
                state=state,
                message=data.message,
                caller_phone=current_user.phone or "",
                channel="web",
            )
        except (openai.RateLimitError, openai.AuthenticationError, openai.APIError) as ai_err:
            logger.warning(f"OpenAI unavailable, using fallback: {ai_err}")
            response = _fallback_response(data.message)

        # Store assistant response
        await orchestrator.conversation_service.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response.message,
        )

        if response.end_conversation:
            outcome = "appointment_scheduled" if response.appointment_booked else "completed"
            await orchestrator.conversation_service.end_conversation(
                conversation_id=conversation.id,
                outcome=outcome,
            )

        return ChatResponse(
            message=response.message,
            conversation_id=conversation.id,
            end_conversation=response.end_conversation,
            appointment_booked=response.appointment_booked,
        )

    except (openai.RateLimitError, openai.AuthenticationError, openai.APIError) as ai_err:
        # Fallback if error happens during conversation creation too
        logger.warning(f"OpenAI error in chat setup: {ai_err}")

        # Try to create a basic conversation without AI
        try:
            conversation = await orchestrator.conversation_service.create_conversation(
                clinic_id=current_clinic.id,
                channel="web",
            )
            fallback = _fallback_response(data.message)
            await orchestrator.conversation_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=fallback.message,
            )
            return ChatResponse(
                message=fallback.message,
                conversation_id=conversation.id,
            )
        except Exception:
            return ChatResponse(
                message="El servicio de IA no esta disponible. Usa el menu lateral para gestionar citas y clientes.",
                conversation_id=data.conversation_id or UUID("00000000-0000-0000-0000-000000000000"),
            )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")


@router.get("/{conversation_id}/messages")
async def get_chat_messages(
    conversation_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get messages for a chat conversation."""
    conv_service = ConversationService(db)
    messages = await conv_service.get_messages(conversation_id)

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.post("/new", response_model=ChatResponse)
async def start_new_chat(
    current_user: CurrentUser,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Start a new chat conversation and get the greeting."""
    orchestrator = Orchestrator(db, current_clinic)

    conversation = await orchestrator.conversation_service.create_conversation(
        clinic_id=current_clinic.id,
        channel="web",
    )

    greeting = await orchestrator.ai_service.generate_greeting(
        current_clinic.name, "web"
    )

    await orchestrator.conversation_service.add_message(
        conversation_id=conversation.id,
        role="assistant",
        content=greeting,
    )

    return ChatResponse(
        message=greeting,
        conversation_id=conversation.id,
    )
