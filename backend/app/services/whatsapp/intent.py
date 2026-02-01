"""Intent classification for WhatsApp messages."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Intent(str, Enum):
    """Detected user intents."""

    SCHEDULING = "scheduling"  # Wants to book an appointment
    EMERGENCY = "emergency"  # Potential emergency situation
    GREETING = "greeting"  # Just saying hello
    QUESTION = "question"  # General question
    CONFIRMATION = "confirmation"  # Yes/confirm response
    REJECTION = "rejection"  # No/reject response
    FOLLOWUP_RESPONSE = "followup_response"  # Response to follow-up
    UNCLEAR = "unclear"  # Cannot determine intent


@dataclass
class IntentResult:
    """Result of intent classification."""

    intent: Intent
    confidence: float  # 0.0 to 1.0
    matched_keywords: list[str]
    is_emergency_potential: bool = False
    emergency_keywords: list[str] = None

    def __post_init__(self):
        if self.emergency_keywords is None:
            self.emergency_keywords = []


class IntentClassifier:
    """Classifies user messages into intents."""

    # Scheduling keywords
    SCHEDULING_KEYWORDS = [
        "cita", "citas", "agendar", "agenda", "programar", "reservar",
        "consulta", "turno", "disponibilidad", "horario", "horarios",
        "atender", "atención", "ver al doctor", "ver al veterinario",
        "llevar a mi", "traer a mi", "revisar a", "vacuna", "vacunar",
        "desparasitar", "chequeo", "control"
    ]

    # Emergency keywords - high confidence
    EMERGENCY_KEYWORDS_HIGH = [
        "veneno", "envenenado", "envenenamiento",
        "atropellado", "atropelló", "atropello", "carro", "coche",
        "no respira", "no puede respirar", "asfixia", "ahogando",
        "convulsión", "convulsiones", "convulsionando",
        "sangre", "sangrando", "hemorragia", "sangrado",
        "no se mueve", "inconsciente", "desmayado", "desmayó",
        "parto", "dando a luz", "no puede parir", "pariendo",
        "mordido", "mordedura", "pelea", "peleó"
    ]

    # Emergency keywords - medium confidence
    EMERGENCY_KEYWORDS_MEDIUM = [
        "urgente", "emergencia", "ayuda", "socorro",
        "muy mal", "grave", "crítico", "muriendo",
        "vomitando sangre", "diarrea con sangre",
        "hinchado", "inflamado", "hinchazón",
        "no come", "no quiere comer", "dejó de comer",
        "temblando", "tiembla"
    ]

    # Greeting keywords
    GREETING_KEYWORDS = [
        "hola", "buenos días", "buenas tardes", "buenas noches",
        "buen día", "hey", "hi", "saludos"
    ]

    # Confirmation keywords
    CONFIRMATION_KEYWORDS = [
        "sí", "si", "confirmo", "correcto", "ok", "okay", "vale",
        "de acuerdo", "acepto", "está bien", "perfecto", "listo",
        "claro", "por supuesto", "afirmativo"
    ]

    # Rejection keywords
    REJECTION_KEYWORDS = [
        "no", "nop", "nel", "cancelar", "cancela", "no quiero",
        "mejor no", "cambiar", "otra", "otro", "diferente"
    ]

    def classify(self, message: str) -> IntentResult:
        """Classify a message into an intent."""
        message_lower = message.lower().strip()

        # Check for emergency first (highest priority)
        emergency_result = self._check_emergency(message_lower)
        if emergency_result.is_emergency_potential:
            return emergency_result

        # Check for confirmation/rejection (quick responses)
        if self._is_short_message(message_lower):
            confirm_result = self._check_confirmation(message_lower)
            if confirm_result.confidence > 0.7:
                return confirm_result

            reject_result = self._check_rejection(message_lower)
            if reject_result.confidence > 0.7:
                return reject_result

        # Check for scheduling intent
        scheduling_result = self._check_scheduling(message_lower)
        if scheduling_result.confidence > 0.5:
            return scheduling_result

        # Check for greeting
        greeting_result = self._check_greeting(message_lower)
        if greeting_result.confidence > 0.7:
            return greeting_result

        # Default to unclear
        return IntentResult(
            intent=Intent.UNCLEAR,
            confidence=0.3,
            matched_keywords=[]
        )

    def _is_short_message(self, message: str) -> bool:
        """Check if message is short (likely a response)."""
        return len(message.split()) <= 3

    def _check_emergency(self, message: str) -> IntentResult:
        """Check for emergency indicators."""
        high_matches = [kw for kw in self.EMERGENCY_KEYWORDS_HIGH if kw in message]
        medium_matches = [kw for kw in self.EMERGENCY_KEYWORDS_MEDIUM if kw in message]

        all_matches = high_matches + medium_matches

        # High confidence emergency
        if high_matches:
            return IntentResult(
                intent=Intent.EMERGENCY,
                confidence=0.9,
                matched_keywords=all_matches,
                is_emergency_potential=True,
                emergency_keywords=all_matches
            )

        # Medium confidence emergency (multiple keywords or with exclamation)
        if len(medium_matches) >= 2 or (medium_matches and '!' in message):
            return IntentResult(
                intent=Intent.EMERGENCY,
                confidence=0.7,
                matched_keywords=all_matches,
                is_emergency_potential=True,
                emergency_keywords=all_matches
            )

        # Single medium keyword - not enough
        if medium_matches:
            return IntentResult(
                intent=Intent.UNCLEAR,
                confidence=0.4,
                matched_keywords=medium_matches,
                is_emergency_potential=False
            )

        return IntentResult(
            intent=Intent.UNCLEAR,
            confidence=0.0,
            matched_keywords=[],
            is_emergency_potential=False
        )

    def _check_scheduling(self, message: str) -> IntentResult:
        """Check for scheduling intent."""
        matches = [kw for kw in self.SCHEDULING_KEYWORDS if kw in message]

        if matches:
            confidence = min(0.5 + len(matches) * 0.15, 0.95)
            return IntentResult(
                intent=Intent.SCHEDULING,
                confidence=confidence,
                matched_keywords=matches
            )

        return IntentResult(
            intent=Intent.UNCLEAR,
            confidence=0.0,
            matched_keywords=[]
        )

    def _check_greeting(self, message: str) -> IntentResult:
        """Check for greeting intent."""
        matches = [kw for kw in self.GREETING_KEYWORDS if kw in message]

        if matches:
            # Pure greeting (just "hola" or similar)
            words = message.split()
            if len(words) <= 2:
                return IntentResult(
                    intent=Intent.GREETING,
                    confidence=0.9,
                    matched_keywords=matches
                )
            # Greeting with more text
            return IntentResult(
                intent=Intent.GREETING,
                confidence=0.6,
                matched_keywords=matches
            )

        return IntentResult(
            intent=Intent.UNCLEAR,
            confidence=0.0,
            matched_keywords=[]
        )

    def _check_confirmation(self, message: str) -> IntentResult:
        """Check for confirmation intent."""
        matches = [kw for kw in self.CONFIRMATION_KEYWORDS if kw in message]

        if matches:
            return IntentResult(
                intent=Intent.CONFIRMATION,
                confidence=0.9,
                matched_keywords=matches
            )

        return IntentResult(
            intent=Intent.UNCLEAR,
            confidence=0.0,
            matched_keywords=[]
        )

    def _check_rejection(self, message: str) -> IntentResult:
        """Check for rejection intent."""
        # Exact "no" match (to avoid false positives)
        if message.strip() == "no" or message.startswith("no "):
            return IntentResult(
                intent=Intent.REJECTION,
                confidence=0.9,
                matched_keywords=["no"]
            )

        matches = [kw for kw in self.REJECTION_KEYWORDS if kw in message]

        if matches:
            return IntentResult(
                intent=Intent.REJECTION,
                confidence=0.8,
                matched_keywords=matches
            )

        return IntentResult(
            intent=Intent.UNCLEAR,
            confidence=0.0,
            matched_keywords=[]
        )

    def parse_slot_selection(
        self,
        message: str,
        num_options: int
    ) -> Optional[int]:
        """
        Parse user's selection from offered slots.
        Returns 0-indexed slot number or None if cannot parse.
        """
        message_lower = message.lower().strip()

        # Direct number selection
        number_patterns = [
            (r'^1$|primera|opción\s*1|uno|la\s*1', 0),
            (r'^2$|segunda|opción\s*2|dos|la\s*2', 1),
            (r'^3$|tercera|opción\s*3|tres|la\s*3', 2),
            (r'^4$|cuarta|opción\s*4|cuatro|la\s*4', 3),
        ]

        for pattern, index in number_patterns:
            if re.search(pattern, message_lower) and index < num_options:
                return index

        return None
