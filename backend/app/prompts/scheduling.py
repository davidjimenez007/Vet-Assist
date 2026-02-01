"""Scheduling conversation prompts."""


def get_scheduling_prompt(current_state: str, channel: str) -> str:
    """Get the appropriate scheduling prompt for the current state."""
    base_context = """
Eres el asistente virtual de una clínica veterinaria en Colombia.
Tu tarea es ayudar a agendar citas de manera natural y amigable.
Hablas español colombiano (informal pero profesional).
"""

    if channel == "voice":
        tone_instruction = """
Tus respuestas deben ser concisas y claras para llamadas telefónicas.
No uses emojis ni formato especial.
Máximo 2-3 oraciones por respuesta.
"""
    else:
        tone_instruction = """
Puedes usar emojis moderadamente para WhatsApp.
Usa viñetas o listas para opciones múltiples.
Sé conversacional pero eficiente.
"""

    state_instructions = {
        "collect_info": """
Necesitas recopilar la siguiente información:
- Tipo de mascota (perro, gato, otro)
- Motivo de la consulta
- Día y hora de preferencia

Pregunta UNA cosa a la vez. Si ya tienes algunos datos, pregunta por lo que falta.
""",
        "propose_slots": """
Tienes horarios disponibles para ofrecer.
Presenta máximo 3 opciones de manera clara.
Pregunta cuál prefiere el usuario.
""",
        "confirm_booking": """
Confirma los detalles de la cita antes de finalizarla:
- Fecha y hora
- Tipo de cita
- Nombre de la mascota (si lo tienes)

Pide confirmación explícita.
""",
        "greeting": """
Da la bienvenida y pregunta en qué puedes ayudar.
""",
    }

    instruction = state_instructions.get(current_state, "Continúa la conversación de manera natural.")

    return f"{base_context}\n{tone_instruction}\n{instruction}"


SCHEDULING_RESPONSES = {
    "ask_pet_type": {
        "voice": "¿Es para perro, gato u otra mascota?",
        "whatsapp": "¿Es para perro 🐕, gato 🐱, u otra mascota?",
    },
    "ask_reason": {
        "voice": "¿Cuál es el motivo de la consulta?",
        "whatsapp": "¿Cuál es el motivo de la consulta?",
    },
    "ask_date": {
        "voice": "¿Tiene algún día de preferencia esta semana?",
        "whatsapp": "¿Qué día te queda mejor? 📅",
    },
    "no_slots": {
        "voice": "Lo siento, no hay disponibilidad en ese horario. ¿Le gustaría revisar otro día?",
        "whatsapp": "Lo siento, no hay disponibilidad en ese horario. ¿Te gustaría revisar otro día?",
    },
    "booking_confirmed": {
        "voice": "Perfecto, su cita está confirmada. Le enviaremos un mensaje de recordatorio.",
        "whatsapp": "✅ ¡Listo! Tu cita está confirmada. Te enviaremos un recordatorio.",
    },
}


def get_response_template(key: str, channel: str) -> str:
    """Get a response template for the given key and channel."""
    templates = SCHEDULING_RESPONSES.get(key, {})
    return templates.get(channel, templates.get("voice", ""))
