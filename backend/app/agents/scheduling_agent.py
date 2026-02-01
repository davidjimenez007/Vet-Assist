"""Scheduling agent for appointment booking."""

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from app.services.calendar import CalendarService
from app.services.ai import AIService
from app.schemas.appointment import AppointmentCreate, TimeSlot, BookingResult


def parse_date_string(date_str: str) -> Optional[date]:
    """Parse date string that may be ISO format or relative/natural language.

    Handles: 'tomorrow', 'mañana', 'hoy', 'today', 'pasado mañana',
    'next Monday', 'el lunes', YYYY-MM-DD, DD/MM/YYYY, etc.
    """
    if not date_str:
        return None

    date_str = date_str.strip().lower()
    today = date.today()

    # Try ISO format first
    try:
        return date.fromisoformat(date_str.upper())
    except ValueError:
        pass

    # Relative dates
    relative_map = {
        'today': 0, 'hoy': 0,
        'tomorrow': 1, 'mañana': 1,
        'pasado mañana': 2, 'day after tomorrow': 2,
    }

    for keyword, days in relative_map.items():
        if keyword in date_str:
            return today + timedelta(days=days)

    # Days of week (Spanish and English)
    days_es = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    days_en = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    for i, (day_es, day_en) in enumerate(zip(days_es, days_en)):
        if day_es in date_str or day_en in date_str:
            # Find next occurrence of this weekday
            days_ahead = i - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

    # Try DD/MM/YYYY or DD-MM-YYYY
    for pattern, fmt in [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', '%d/%m/%Y'),
        (r'(\d{1,2})[/-](\d{1,2})', '%d/%m'),
    ]:
        match = re.search(pattern, date_str)
        if match:
            try:
                if len(match.groups()) == 3:
                    return datetime.strptime(f"{match.group(1)}/{match.group(2)}/{match.group(3)}", '%d/%m/%Y').date()
                else:
                    parsed = datetime.strptime(f"{match.group(1)}/{match.group(2)}", '%d/%m')
                    return parsed.replace(year=today.year).date()
            except ValueError:
                continue

    return None


@dataclass
class SchedulingState:
    """Current state of the scheduling process."""

    pet_type: Optional[str] = None
    pet_name: Optional[str] = None
    reason: Optional[str] = None
    preferred_date: Optional[date] = None
    preferred_time: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    proposed_slots: Optional[list[TimeSlot]] = None
    selected_slot: Optional[TimeSlot] = None

    def missing_fields(self) -> list[str]:
        """Get list of missing required fields."""
        missing = []
        if not self.pet_type:
            missing.append("pet_type")
        if not self.reason:
            missing.append("reason")
        if not self.preferred_date:
            missing.append("preferred_date")
        return missing

    def is_complete(self) -> bool:
        """Check if we have all required info for booking."""
        return (
            self.pet_type is not None
            and self.reason is not None
            and self.selected_slot is not None
            and self.client_phone is not None
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "pet_type": self.pet_type,
            "pet_name": self.pet_name,
            "reason": self.reason,
            "preferred_date": self.preferred_date.isoformat() if self.preferred_date else None,
            "preferred_time": self.preferred_time,
            "client_name": self.client_name,
            "client_phone": self.client_phone,
        }
        # Include proposed slots for state persistence
        if self.proposed_slots:
            result["proposed_slots"] = [
                {"start": s.start, "end": s.end} for s in self.proposed_slots
            ]
        if self.selected_slot:
            result["selected_slot"] = {
                "start": self.selected_slot.start,
                "end": self.selected_slot.end,
            }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "SchedulingState":
        """Create from dictionary."""
        preferred_date = data.get("preferred_date")
        if preferred_date and isinstance(preferred_date, str):
            preferred_date = parse_date_string(preferred_date)
        elif preferred_date and isinstance(preferred_date, date):
            pass  # Already a date object

        # Restore proposed_slots
        proposed_slots = None
        if data.get("proposed_slots"):
            proposed_slots = [
                TimeSlot(start=s["start"], end=s["end"])
                for s in data["proposed_slots"]
            ]

        # Restore selected_slot
        selected_slot = None
        if data.get("selected_slot"):
            selected_slot = TimeSlot(
                start=data["selected_slot"]["start"],
                end=data["selected_slot"]["end"],
            )

        return cls(
            pet_type=data.get("pet_type"),
            pet_name=data.get("pet_name"),
            reason=data.get("reason"),
            preferred_date=preferred_date,
            preferred_time=data.get("preferred_time"),
            client_name=data.get("client_name"),
            client_phone=data.get("client_phone"),
            proposed_slots=proposed_slots,
            selected_slot=selected_slot,
        )


class SchedulingAgent:
    """Agent for handling appointment scheduling with contextual AI reasoning."""

    def __init__(
        self,
        calendar_service: CalendarService,
        ai_service: Optional[AIService] = None,
    ):
        self.calendar = calendar_service
        self.ai = ai_service or AIService()

    async def process_message(
        self,
        message: str,
        state: SchedulingState,
        clinic_id: UUID,
        conversation_history: Optional[list[dict]] = None,
        channel: str = "web",
    ) -> tuple[SchedulingState, str, bool]:
        """
        Process a user message and update scheduling state with contextual reasoning.

        Returns:
            - Updated state
            - Response message
            - Whether to proceed to booking
        """
        # Extract data from message with conversation context
        current_data = state.to_dict()
        updated_data = await self.ai.extract_scheduling_data(
            message, current_data, conversation_history
        )

        # Update state with extracted data
        new_state = SchedulingState.from_dict(updated_data)
        new_state.client_phone = state.client_phone  # Preserve phone

        # Check what's missing
        missing = new_state.missing_fields()

        # If we have proposed slots, check if user is selecting one
        if new_state.proposed_slots:
            # Use AI to understand slot selection
            slot_result = await self.ai.process_slot_selection(
                message,
                [{"start": s.start, "end": s.end} for s in new_state.proposed_slots],
                current_data,
            )

            if slot_result.get("matched_slot"):
                # User selected a slot
                selected = self._match_slot(slot_result["matched_slot"], new_state.proposed_slots)
                if selected:
                    new_state.selected_slot = selected
                    # Generate confirmation and proceed to booking
                    return new_state, "", True

            # If user mentioned a time preference that doesn't match, try direct matching
            if new_state.preferred_time:
                selected = self._match_slot(new_state.preferred_time, new_state.proposed_slots)
                if selected:
                    new_state.selected_slot = selected
                    return new_state, "", True

            # User didn't select a slot, generate contextual response
            slots_dict = [{"start": s.start, "end": s.end} for s in new_state.proposed_slots]
            response = await self.ai.generate_scheduling_response(
                user_message=message,
                collected_data=new_state.to_dict(),
                available_slots=slots_dict,
                conversation_history=conversation_history,
                channel=channel,
            )
            return new_state, response, False

        # If we have enough info to look up slots
        if not missing and new_state.preferred_date and not new_state.proposed_slots:
            slots = await self.calendar.find_available_slots(
                clinic_id=clinic_id,
                target_date=new_state.preferred_date,
            )

            if slots:
                new_state.proposed_slots = slots[:5]  # Max 5 options
                # Generate contextual response with available slots
                slots_dict = [{"start": s.start, "end": s.end} for s in slots[:5]]
                response = await self.ai.generate_scheduling_response(
                    user_message=message,
                    collected_data=new_state.to_dict(),
                    available_slots=slots_dict,
                    conversation_history=conversation_history,
                    channel=channel,
                )
            else:
                # No slots on preferred date, find next available
                next_available = await self.calendar.get_next_available(clinic_id)
                if next_available:
                    response = (
                        f"No hay disponibilidad el {new_state.preferred_date.strftime('%d/%m')}. "
                        f"El próximo horario disponible es el {next_available['date']} "
                        f"a las {next_available['time']}. ¿Le sirve?"
                    )
                else:
                    response = (
                        "Lo siento, no hay disponibilidad en los próximos días. "
                        "¿Desea que un humano le devuelva la llamada?"
                    )

            return new_state, response, False

        # Still collecting info - generate contextual clarification
        if missing:
            response = await self.ai.generate_clarification(
                missing_fields=missing,
                collected_data=new_state.to_dict(),
                user_message=message,
                channel=channel,
            )
            return new_state, response, False

        # Fallback: generate general scheduling response
        response = await self.ai.generate_scheduling_response(
            user_message=message,
            collected_data=new_state.to_dict(),
            available_slots=None,
            conversation_history=conversation_history,
            channel=channel,
        )
        return new_state, response, False

    async def book(
        self,
        state: SchedulingState,
        clinic_id: UUID,
        conversation_id: Optional[UUID] = None,
    ) -> BookingResult:
        """Book the appointment with current state."""
        if not state.is_complete():
            return BookingResult(
                success=False,
                error="INCOMPLETE_INFO",
                confirmation_message="Faltan datos para completar la cita.",
            )

        # Build start time from selected slot and date
        slot_parts = state.selected_slot.start.split(":")
        start_time = datetime.combine(
            state.preferred_date,
            datetime.strptime(state.selected_slot.start, "%H:%M").time(),
        )

        appointment_data = AppointmentCreate(
            client_phone=state.client_phone,
            client_name=state.client_name,
            pet_type=state.pet_type,
            pet_name=state.pet_name,
            reason=state.reason,
            start_time=start_time,
            source="ai_voice",
            conversation_id=conversation_id,
        )

        return await self.calendar.book_appointment(clinic_id, appointment_data)

    def _format_slot_options(
        self, slots: list[TimeSlot], target_date: date
    ) -> str:
        """Format slot options for voice response."""
        if len(slots) == 1:
            return f"Tenemos disponibilidad a las {self._format_time(slots[0].start)}. ¿Le queda bien?"

        formatted_times = [self._format_time(s.start) for s in slots]

        if len(slots) == 2:
            return f"Tenemos disponibilidad a las {formatted_times[0]} y a las {formatted_times[1]}. ¿Cuál prefiere?"

        times_str = ", ".join(formatted_times[:-1]) + f" y a las {formatted_times[-1]}"
        return f"Tenemos disponibilidad a las {times_str}. ¿Cuál le queda mejor?"

    def _format_time(self, time_str: str) -> str:
        """Format time for voice (e.g., '10:00' -> '10 de la mañana')."""
        hour, minute = map(int, time_str.split(":"))

        if hour < 12:
            period = "de la mañana"
        elif hour < 18:
            period = "de la tarde"
        else:
            period = "de la noche"

        if hour > 12:
            hour -= 12

        if minute == 0:
            return f"{hour} {period}"
        elif minute == 30:
            return f"{hour} y media {period}"
        else:
            return f"{hour}:{minute:02d} {period}"

    def _match_slot(
        self, time_str: str, available_slots: list[TimeSlot]
    ) -> Optional[TimeSlot]:
        """Match user's time preference to available slots."""
        # Normalize time string
        time_lower = time_str.lower()

        for slot in available_slots:
            slot_hour = int(slot.start.split(":")[0])

            # Check for exact match
            if time_str in slot.start:
                return slot

            # Check for hour match
            if str(slot_hour) in time_str or str(slot_hour % 12) in time_str:
                return slot

            # Check for keywords
            if "primera" in time_lower and slot == available_slots[0]:
                return slot
            if "segunda" in time_lower and len(available_slots) > 1 and slot == available_slots[1]:
                return slot
            if "tercera" in time_lower and len(available_slots) > 2 and slot == available_slots[2]:
                return slot

        return None
