"""Intent detection agent."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

from app.services.ai import AIService


class Intent(str, Enum):
    """Possible user intents."""

    SCHEDULE = "SCHEDULE"
    EMERGENCY = "EMERGENCY"
    QUESTION = "QUESTION"
    UNCLEAR = "UNCLEAR"


@dataclass
class IntentResult:
    """Result of intent detection."""

    intent: Intent
    confidence: float
    extracted_data: dict
    is_emergency: bool = False
    urgency_level: str = "none"
    symptoms: list[str] = None

    def __post_init__(self):
        if self.symptoms is None:
            self.symptoms = []


class IntentAgent:
    """Agent for detecting user intent from messages."""

    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai = ai_service or AIService()

    async def detect(
        self,
        message: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> IntentResult:
        """Detect user intent from a message."""
        # First, check for emergency
        emergency_result = await self.ai.detect_emergency(message, conversation_history)

        is_emergency = emergency_result.get("is_emergency", False)
        urgency_level = emergency_result.get("urgency_level", "none")
        symptoms = emergency_result.get("symptoms", [])

        if is_emergency and urgency_level in ["critical", "high"]:
            return IntentResult(
                intent=Intent.EMERGENCY,
                confidence=0.95,
                extracted_data={"symptoms": symptoms},
                is_emergency=True,
                urgency_level=urgency_level,
                symptoms=symptoms,
            )

        # Regular intent detection
        intent_result = await self.ai.detect_intent(message, conversation_history)

        intent_str = intent_result.get("intent", "UNCLEAR")
        try:
            intent = Intent(intent_str)
        except ValueError:
            intent = Intent.UNCLEAR

        return IntentResult(
            intent=intent,
            confidence=intent_result.get("confidence", 0.5),
            extracted_data=intent_result.get("extracted_data", {}),
            is_emergency=is_emergency,
            urgency_level=urgency_level,
            symptoms=symptoms,
        )

    async def refine_intent(
        self,
        previous_intent: IntentResult,
        new_message: str,
        conversation_history: list[dict],
    ) -> IntentResult:
        """Refine intent based on follow-up messages."""
        # If we already have a strong intent, only update if contradicted
        if previous_intent.confidence > 0.8 and previous_intent.intent != Intent.UNCLEAR:
            # Check if new message changes the intent
            new_result = await self.detect(new_message, conversation_history)

            if new_result.confidence > previous_intent.confidence:
                return new_result
            else:
                # Update extracted data only
                merged_data = {**previous_intent.extracted_data}
                merged_data.update(new_result.extracted_data)
                return IntentResult(
                    intent=previous_intent.intent,
                    confidence=previous_intent.confidence,
                    extracted_data=merged_data,
                    is_emergency=previous_intent.is_emergency or new_result.is_emergency,
                    urgency_level=(
                        new_result.urgency_level
                        if new_result.is_emergency
                        else previous_intent.urgency_level
                    ),
                    symptoms=list(set(previous_intent.symptoms + new_result.symptoms)),
                )

        return await self.detect(new_message, conversation_history)
