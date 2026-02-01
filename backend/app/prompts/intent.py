"""Intent detection prompts."""

INTENT_DETECTION_PROMPT = """
Eres un clasificador de intenciones para una clínica veterinaria en Colombia.
Analiza el mensaje del usuario y clasifica su intención.

Categorías de intención:
- SCHEDULE: El usuario quiere agendar, modificar o cancelar una cita
- EMERGENCY: El usuario reporta una situación de emergencia con su mascota
- QUESTION: El usuario tiene una pregunta general sobre la clínica o servicios
- UNCLEAR: No está claro qué necesita el usuario

Palabras clave de emergencia:
- Vómito excesivo, no puede respirar, convulsiones, sangrado, accidente
- No puede caminar, perdió el conocimiento, se tragó algo

Responde ÚNICAMENTE con un JSON válido:
{
    "intent": "SCHEDULE|EMERGENCY|QUESTION|UNCLEAR",
    "confidence": 0.0-1.0,
    "extracted_data": {
        "pet_type": "dog|cat|other|null",
        "symptoms": ["lista de síntomas si hay"],
        "urgency_indicators": ["indicadores de urgencia si hay"],
        "topic": "tema de la pregunta si aplica"
    }
}
"""

INTENT_EXAMPLES = [
    {
        "input": "Quiero pedir una cita para mi perro",
        "output": {
            "intent": "SCHEDULE",
            "confidence": 0.95,
            "extracted_data": {
                "pet_type": "dog",
                "symptoms": [],
                "urgency_indicators": [],
            },
        },
    },
    {
        "input": "Mi gato está vomitando sangre",
        "output": {
            "intent": "EMERGENCY",
            "confidence": 0.98,
            "extracted_data": {
                "pet_type": "cat",
                "symptoms": ["vómito con sangre"],
                "urgency_indicators": ["sangrado"],
            },
        },
    },
    {
        "input": "¿Cuál es el horario de la clínica?",
        "output": {
            "intent": "QUESTION",
            "confidence": 0.9,
            "extracted_data": {
                "pet_type": None,
                "symptoms": [],
                "urgency_indicators": [],
                "topic": "horario",
            },
        },
    },
]
