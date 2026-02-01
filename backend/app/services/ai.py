"""AI service for intelligent conversation handling."""

import json
import logging
import re
from datetime import date, datetime
from typing import Optional
import openai

from app.config import settings
from app.prompts import intent as intent_prompts
from app.prompts import emergency as emergency_prompts

logger = logging.getLogger(__name__)


def extract_json(text: str) -> Optional[dict]:
    """Extract JSON from text that may contain markdown code blocks or extra text."""
    if not text:
        return None

    # First, try to parse as-is (pure JSON)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code block
    code_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    match = re.search(code_block_pattern, text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in the text
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # Last resort: find anything between first { and last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    return None


class AIService:
    """Service for AI-powered conversation handling with contextual reasoning."""

    def __init__(self):
        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        self.client = openai.AsyncOpenAI(**client_kwargs)
        self.model = settings.openai_model

    async def _call_gpt(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Make a call to the LLM with conversation context."""
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except openai.RateLimitError:
            logger.warning("Rate limit exceeded")
            raise
        except openai.AuthenticationError:
            logger.error("Authentication failed")
            raise
        except Exception as e:
            logger.error(f"API error: {e}")
            raise

    async def detect_intent(
        self, user_message: str, conversation_history: Optional[list[dict]] = None
    ) -> dict:
        """Detect user intent with context awareness."""
        system_prompt = intent_prompts.INTENT_DETECTION_PROMPT

        response = await self._call_gpt(
            system_prompt=system_prompt,
            user_message=user_message,
            conversation_history=conversation_history,
            temperature=0.3,
        )

        logger.debug(f"Intent detection raw response: {response}")

        result = extract_json(response)
        if result is None:
            logger.warning(f"Failed to parse intent JSON from: {response[:200]}")
            result = {
                "intent": "UNCLEAR",
                "confidence": 0.5,
                "extracted_data": {},
            }
        else:
            logger.info(f"Detected intent: {result.get('intent')} (confidence: {result.get('confidence')})")

        return result

    async def detect_emergency(
        self, user_message: str, conversation_history: Optional[list[dict]] = None
    ) -> dict:
        """Detect if the message indicates an emergency."""
        system_prompt = emergency_prompts.EMERGENCY_DETECTION_PROMPT

        response = await self._call_gpt(
            system_prompt=system_prompt,
            user_message=user_message,
            conversation_history=conversation_history,
            temperature=0.2,
        )

        logger.debug(f"Emergency detection raw response: {response}")

        result = extract_json(response)
        if result is None:
            logger.warning(f"Failed to parse emergency JSON from: {response[:200]}")
            result = {
                "is_emergency": False,
                "urgency_level": "low",
                "symptoms": [],
            }
        else:
            logger.info(f"Emergency check: is_emergency={result.get('is_emergency')}, level={result.get('urgency_level')}")

        return result

    async def generate_greeting(self, clinic_name: str, channel: str) -> str:
        """Generate a greeting message."""
        if channel == "voice":
            return (
                f"{clinic_name}, buenos días. Soy el asistente virtual. "
                "¿En qué puedo ayudarle hoy?"
            )
        else:
            return (
                f"¡Hola! Soy el asistente de {clinic_name}. "
                "¿En qué puedo ayudarte hoy?"
            )

    async def generate_scheduling_response(
        self,
        user_message: str,
        collected_data: dict,
        available_slots: Optional[list[dict]] = None,
        conversation_history: Optional[list[dict]] = None,
        channel: str = "web",
    ) -> str:
        """Generate an intelligent scheduling response based on context.

        This method reasons about:
        - What the user just said
        - What information we already have
        - What's still missing
        - What appointment slots are available
        """
        today = date.today()

        # Build context about collected data
        collected_info = []
        missing_info = []

        if collected_data.get("pet_type"):
            pet_names = {"dog": "perro", "cat": "gato", "other": "mascota"}
            collected_info.append(f"Mascota: {pet_names.get(collected_data['pet_type'], collected_data['pet_type'])}")
        else:
            missing_info.append("tipo de mascota (perro, gato, otro)")

        if collected_data.get("pet_name"):
            collected_info.append(f"Nombre: {collected_data['pet_name']}")

        if collected_data.get("reason"):
            collected_info.append(f"Motivo: {collected_data['reason']}")
        else:
            missing_info.append("motivo de la consulta")

        if collected_data.get("preferred_date"):
            collected_info.append(f"Fecha preferida: {collected_data['preferred_date']}")
        else:
            missing_info.append("día de preferencia")

        # Format available slots
        slots_text = ""
        if available_slots and len(available_slots) > 0:
            slot_times = [s.get("start", s) if isinstance(s, dict) else str(s) for s in available_slots[:5]]
            slots_text = f"Horarios disponibles: {', '.join(slot_times)}"

        system_prompt = f"""Eres el asistente virtual de una clínica veterinaria en Colombia.
Tu personalidad es amigable, profesional y eficiente. Hablas español colombiano informal pero respetuoso.

CONTEXTO DE LA CONVERSACIÓN:
- Fecha de hoy: {today.strftime('%A %d de %B de %Y')}
- Canal: {channel}
- Información ya recopilada: {', '.join(collected_info) if collected_info else 'Ninguna aún'}
- Información que falta: {', '.join(missing_info) if missing_info else 'Tenemos toda la información necesaria'}
{slots_text}

INSTRUCCIONES:
1. ANALIZA lo que el usuario acaba de decir y extrae cualquier información relevante
2. RECONOCE lo que el usuario mencionó (no ignores lo que dijo)
3. Si hay horarios disponibles, PRESÉNTALOS de forma clara
4. Si falta información, pregunta por UNA cosa a la vez de manera natural
5. Si el usuario seleccionó un horario, CONFIRMA la selección
6. Sé conciso: máximo 2-3 oraciones

IMPORTANTE:
- NO repitas información que el usuario ya dio
- NO hagas múltiples preguntas a la vez
- SI el usuario menciona una hora específica, verifica si está en los horarios disponibles
- Responde de forma conversacional, no como un formulario"""

        response = await self._call_gpt(
            system_prompt=system_prompt,
            user_message=f"El usuario dice: \"{user_message}\"",
            conversation_history=conversation_history,
            temperature=0.7,
            max_tokens=200,
        )

        return response.strip()

    async def generate_emergency_response(
        self, urgency_level: str, symptoms: list[str], channel: str = "voice"
    ) -> str:
        """Generate a response for emergency situations."""
        system_prompt = emergency_prompts.EMERGENCY_RESPONSE_PROMPT

        context = f"""
Nivel de urgencia: {urgency_level}
Síntomas reportados: {', '.join(symptoms) if symptoms else 'No especificados'}
Canal: {channel}
"""

        response = await self._call_gpt(
            system_prompt=system_prompt,
            user_message=context,
            temperature=0.5,
        )

        return response

    async def answer_question(
        self,
        question: str,
        clinic_info: dict,
        conversation_history: Optional[list[dict]] = None,
    ) -> str:
        """Answer general questions about the clinic with context."""
        system_prompt = f"""Eres el asistente virtual de {clinic_info.get('name', 'la clínica veterinaria')}.
Tu tarea es responder preguntas de manera clara, útil y concisa.

Información de la clínica:
- Horario: {json.dumps(clinic_info.get('working_hours', {}), ensure_ascii=False)}
- Servicios: consultas generales, vacunación, cirugía, peluquería, emergencias

INSTRUCCIONES:
1. Responde directamente a la pregunta del usuario
2. Si la pregunta está relacionada con agendar una cita, ofrece ayudar
3. Si no tienes la información, sé honesto y ofrece alternativas
4. Usa español colombiano amigable
5. Sé conciso pero completo"""

        response = await self._call_gpt(
            system_prompt=system_prompt,
            user_message=question,
            conversation_history=conversation_history,
            temperature=0.7,
        )

        return response

    async def extract_scheduling_data(
        self,
        user_message: str,
        current_data: dict,
        conversation_history: Optional[list[dict]] = None,
    ) -> dict:
        """Extract scheduling-related data from user message with context."""
        today = date.today()

        system_prompt = f"""Extrae información de citas del mensaje del usuario.
Fecha de hoy: {today.isoformat()} ({today.strftime('%A')})

Datos actuales ya recopilados:
{json.dumps(current_data, ensure_ascii=False, indent=2)}

INSTRUCCIONES:
1. Extrae SOLO la información nueva del mensaje
2. Para fechas relativas como "mañana", "el lunes", etc., conviértelas a formato YYYY-MM-DD
3. Para tipos de mascota: usa "dog" para perro, "cat" para gato, "other" para otros
4. Si el usuario dice un horario como "a las 9", extrae "09:00"

Responde SOLO con un JSON válido:
{{
    "pet_type": "dog|cat|other o null si no se menciona",
    "pet_name": "nombre de la mascota o null",
    "reason": "motivo de la cita o null",
    "preferred_date": "YYYY-MM-DD o null",
    "preferred_time": "HH:MM o null",
    "client_name": "nombre del cliente o null"
}}"""

        response = await self._call_gpt(
            system_prompt=system_prompt,
            user_message=user_message,
            conversation_history=conversation_history,
            temperature=0.2,
        )

        logger.debug(f"Scheduling data extraction raw response: {response}")

        extracted = extract_json(response)
        if extracted:
            # Merge with current data, only updating non-null values
            for key, value in extracted.items():
                if value is not None:
                    current_data[key] = value
            logger.info(f"Extracted scheduling data: {extracted}")
        else:
            logger.warning(f"Failed to parse scheduling data from: {response[:200]}")

        return current_data

    async def process_slot_selection(
        self,
        user_message: str,
        available_slots: list[dict],
        collected_data: dict,
    ) -> dict:
        """Process user's slot selection and return matched slot or clarification needed."""
        slots_text = ", ".join([s.get("start", str(s)) if isinstance(s, dict) else str(s) for s in available_slots])

        system_prompt = f"""Analiza si el usuario está seleccionando uno de los horarios disponibles.

Horarios disponibles: {slots_text}

INSTRUCCIONES:
1. Si el usuario menciona un horario específico (ej: "a las 9", "la primera", "9:00"), identifica cuál slot corresponde
2. Si dice "la primera" o "la segunda", cuenta desde el inicio de la lista
3. Si el horario mencionado no está disponible, indica que no hay match

Responde con JSON:
{{
    "matched_slot": "HH:MM del slot seleccionado o null si no hay match",
    "user_intent": "select_slot|unclear|request_different",
    "clarification_needed": true/false
}}"""

        response = await self._call_gpt(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.2,
        )

        result = extract_json(response)
        if result is None:
            result = {
                "matched_slot": None,
                "user_intent": "unclear",
                "clarification_needed": True,
            }

        return result

    async def generate_confirmation_message(
        self,
        appointment_data: dict,
        channel: str = "web",
    ) -> str:
        """Generate a natural confirmation message for a booked appointment."""
        pet_name = appointment_data.get("pet_name", "tu mascota")
        date_str = appointment_data.get("date", "")
        time_str = appointment_data.get("time", "")
        reason = appointment_data.get("reason", "consulta")

        # Parse date for natural format
        try:
            apt_date = datetime.strptime(date_str, "%Y-%m-%d")
            date_formatted = apt_date.strftime("%A %d de %B")
        except:
            date_formatted = date_str

        # Format time naturally
        try:
            hour = int(time_str.split(":")[0])
            minute = time_str.split(":")[1] if ":" in time_str else "00"
            period = "de la mañana" if hour < 12 else "de la tarde"
            display_hour = hour if hour <= 12 else hour - 12
            time_formatted = f"{display_hour}:{minute} {period}"
        except:
            time_formatted = time_str

        if channel == "voice":
            return (
                f"Perfecto, queda confirmada la cita para {pet_name} "
                f"el {date_formatted} a las {time_formatted} para {reason}. "
                "Le enviaremos un recordatorio. ¿Hay algo más en que pueda ayudarle?"
            )
        else:
            return (
                f"✅ ¡Cita confirmada!\n\n"
                f"📅 {date_formatted}\n"
                f"🕐 {time_formatted}\n"
                f"🐾 {pet_name}\n"
                f"📋 {reason}\n\n"
                "Te enviaremos un recordatorio antes de la cita."
            )

    async def generate_clarification(
        self,
        missing_fields: list[str],
        collected_data: dict,
        user_message: str,
        channel: str = "web"
    ) -> str:
        """Generate a contextual clarification request.

        Instead of hardcoded responses, this uses the AI to generate
        natural, context-aware follow-up questions.
        """
        # Build context
        collected_info = []
        if collected_data.get("pet_type"):
            pet_names = {"dog": "perro", "cat": "gato", "other": "mascota"}
            collected_info.append(f"mascota: {pet_names.get(collected_data['pet_type'], 'mascota')}")
        if collected_data.get("pet_name"):
            collected_info.append(f"nombre: {collected_data['pet_name']}")
        if collected_data.get("reason"):
            collected_info.append(f"motivo: {collected_data['reason']}")
        if collected_data.get("preferred_date"):
            collected_info.append(f"fecha: {collected_data['preferred_date']}")

        field_descriptions = {
            "pet_type": "tipo de mascota (perro, gato u otro)",
            "reason": "motivo de la consulta",
            "preferred_date": "día de preferencia para la cita",
            "preferred_time": "hora de preferencia",
            "client_name": "nombre del cliente",
        }

        missing_descriptions = [field_descriptions.get(f, f) for f in missing_fields[:2]]

        system_prompt = f"""Eres el asistente de una clínica veterinaria.
El usuario quiere agendar una cita.

Ya tenemos: {', '.join(collected_info) if collected_info else 'nada aún'}
Necesitamos: {', '.join(missing_descriptions)}

El usuario acaba de decir: "{user_message}"

GENERA una respuesta natural que:
1. Reconozca brevemente lo que el usuario dijo (si es relevante)
2. Pregunte por LA PRIMERA cosa que falta de manera conversacional
3. Sea concisa (1-2 oraciones máximo)
4. Use español colombiano amigable

NO uses formato de lista ni múltiples preguntas."""

        response = await self._call_gpt(
            system_prompt=system_prompt,
            user_message="Genera la respuesta:",
            temperature=0.7,
            max_tokens=100,
        )

        return response.strip()

    async def generate_farewell(self, channel: str, outcome: str) -> str:
        """Generate a farewell message."""
        if outcome == "appointment_scheduled":
            if channel == "voice":
                return (
                    "Gracias por llamar. Le enviaremos un recordatorio. "
                    "¡Que tenga un excelente día!"
                )
            else:
                return (
                    "¡Perfecto! Te enviaremos un recordatorio. "
                    "¿Hay algo más en que pueda ayudarte?"
                )
        else:
            if channel == "voice":
                return "Gracias por llamar. ¡Que tenga un excelente día!"
            else:
                return "¡Gracias por escribirnos! ¡Que tengas un excelente día!"
