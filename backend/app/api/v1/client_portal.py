"""Client portal endpoints for appointments, pets, and chat."""

import logging
from typing import List, Optional
from uuid import UUID

import openai
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentClient, ClientClinic, DBSession
from app.models import Appointment, Pet
from app.schemas.client_auth import (
    AppointmentInfo,
    ClinicInfo,
    PetInfo,
    PortalChatMessage,
    PortalChatResponse,
)
from app.agents.orchestrator import Orchestrator, OrchestratorResponse
from app.services.conversation import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter()


def _fallback_response(message: str) -> OrchestratorResponse:
    """Generate a rule-based fallback when OpenAI is unavailable."""
    msg_lower = message.lower().strip()

    # Scheduling keywords
    schedule_words = ["cita", "agendar", "programar", "reservar", "turno", "consulta"]
    if any(w in msg_lower for w in schedule_words):
        return OrchestratorResponse(
            message=(
                "Entiendo que quieres agendar una cita. En este momento el servicio de IA "
                "no esta disponible. Por favor intenta mas tarde o contacta a la clinica "
                "directamente por telefono."
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
                "Puedes ver tus citas en la seccion de Citas. "
                "Cuando se resuelva la conexion, podre ayudarte a agendar nuevas citas."
            ),
        )

    # Default
    return OrchestratorResponse(
        message=(
            "El servicio de IA esta temporalmente limitado. "
            "Puedes ver tus citas programadas en la seccion de Citas."
        ),
    )


@router.get("/appointments", response_model=List[AppointmentInfo])
async def get_client_appointments(
    current_client: CurrentClient,
    db: DBSession,
    status: Optional[str] = None,
):
    """Get appointments for the current client."""
    query = select(Appointment).where(Appointment.client_id == current_client.id)

    if status:
        query = query.where(Appointment.status == status)

    query = query.order_by(Appointment.start_time.desc())

    result = await db.execute(query)
    appointments = result.scalars().all()

    response = []
    for apt in appointments:
        # Get pet info if available
        pet_name = None
        pet_species = None
        if apt.pet_id:
            pet_result = await db.execute(select(Pet).where(Pet.id == apt.pet_id))
            pet = pet_result.scalar_one_or_none()
            if pet:
                pet_name = pet.name
                pet_species = pet.species

        response.append(
            AppointmentInfo(
                id=apt.id,
                pet_name=pet_name,
                pet_species=pet_species,
                scheduled_at=apt.start_time.isoformat(),
                duration_minutes=apt.duration_minutes,
                reason=apt.reason,
                status=apt.status,
                notes=apt.notes,
            )
        )

    return response


@router.get("/pets", response_model=List[PetInfo])
async def get_client_pets(
    current_client: CurrentClient,
    db: DBSession,
):
    """Get pets for the current client."""
    result = await db.execute(
        select(Pet).where(Pet.client_id == current_client.id)
    )
    pets = result.scalars().all()

    return [
        PetInfo(
            id=pet.id,
            name=pet.name,
            species=pet.species,
            breed=pet.breed,
        )
        for pet in pets
    ]


@router.get("/clinic", response_model=ClinicInfo)
async def get_clinic_info(
    current_clinic: ClientClinic,
):
    """Get basic clinic information."""
    return ClinicInfo(
        id=current_clinic.id,
        name=current_clinic.name,
        phone=current_clinic.phone,
        address=current_clinic.address if hasattr(current_clinic, 'address') else None,
    )


@router.post("/chat", response_model=PortalChatResponse)
async def send_portal_chat_message(
    data: PortalChatMessage,
    current_client: CurrentClient,
    current_clinic: ClientClinic,
    db: DBSession,
):
    """Send a message to the AI assistant via client portal."""
    orchestrator = Orchestrator(db, current_clinic)

    try:
        if data.conversation_id:
            conversation = await orchestrator.conversation_service.get_conversation(
                data.conversation_id
            )
            # Verify this conversation belongs to the client
            if not conversation or conversation.client_id != current_client.id:
                conversation = None

            if not conversation or conversation.status != "active":
                conversation = await orchestrator.conversation_service.create_conversation(
                    clinic_id=current_clinic.id,
                    client_id=current_client.id,
                    channel="web_portal",
                )
        else:
            conversation = await orchestrator.conversation_service.create_conversation(
                clinic_id=current_clinic.id,
                client_id=current_client.id,
                channel="web_portal",
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

        # Process through orchestrator
        try:
            response = await orchestrator._process_input(
                state=state,
                message=data.message,
                caller_phone=current_client.phone,
                channel="web_portal",
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

        return PortalChatResponse(
            message=response.message,
            conversation_id=conversation.id,
            end_conversation=response.end_conversation,
            appointment_booked=response.appointment_booked,
        )

    except (openai.RateLimitError, openai.AuthenticationError, openai.APIError) as ai_err:
        logger.warning(f"OpenAI error in chat setup: {ai_err}")

        try:
            conversation = await orchestrator.conversation_service.create_conversation(
                clinic_id=current_clinic.id,
                client_id=current_client.id,
                channel="web_portal",
            )
            fallback = _fallback_response(data.message)
            await orchestrator.conversation_service.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=fallback.message,
            )
            return PortalChatResponse(
                message=fallback.message,
                conversation_id=conversation.id,
            )
        except Exception:
            return PortalChatResponse(
                message="El servicio de IA no esta disponible. Por favor intenta mas tarde.",
                conversation_id=data.conversation_id or UUID("00000000-0000-0000-0000-000000000000"),
            )

    except Exception as e:
        logger.error(f"Portal chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")


@router.post("/chat/new", response_model=PortalChatResponse)
async def start_new_portal_chat(
    current_client: CurrentClient,
    current_clinic: ClientClinic,
    db: DBSession,
):
    """Start a new chat conversation for the client portal."""
    orchestrator = Orchestrator(db, current_clinic)

    conversation = await orchestrator.conversation_service.create_conversation(
        clinic_id=current_clinic.id,
        client_id=current_client.id,
        channel="web_portal",
    )

    try:
        greeting = await orchestrator.ai_service.generate_greeting(
            current_clinic.name, "web"
        )
    except (openai.RateLimitError, openai.AuthenticationError, openai.APIError):
        greeting = (
            f"Hola! Bienvenido al portal de {current_clinic.name}. "
            "En este momento el asistente virtual esta limitado, pero puedes "
            "ver tus citas programadas en la seccion de Citas."
        )

    await orchestrator.conversation_service.add_message(
        conversation_id=conversation.id,
        role="assistant",
        content=greeting,
    )

    return PortalChatResponse(
        message=greeting,
        conversation_id=conversation.id,
    )


@router.get("/chat/{conversation_id}/messages")
async def get_portal_chat_messages(
    conversation_id: UUID,
    current_client: CurrentClient,
    db: DBSession,
):
    """Get messages for a chat conversation."""
    conv_service = ConversationService(db)
    conversation = await conv_service.get_conversation(conversation_id)

    # Verify the conversation belongs to this client
    if not conversation or conversation.client_id != current_client.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

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
