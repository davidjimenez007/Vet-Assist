"""Conversation state machine definitions."""

from enum import Enum
from datetime import timedelta
from typing import Optional


class ConversationState(str, Enum):
    """All possible conversation states."""

    # Initial states
    IDLE = "IDLE"
    GREETING = "GREETING"
    INTENT_DETECTION = "INTENT_DETECTION"

    # Scheduling flow
    ASK_REASON = "ASK_REASON"
    OFFER_SLOTS = "OFFER_SLOTS"
    AWAIT_SELECTION = "AWAIT_SELECTION"
    CONFIRM_BOOKING = "CONFIRM_BOOKING"

    # Emergency flow
    CONFIRM_EMERGENCY = "CONFIRM_EMERGENCY"
    ESCALATE = "ESCALATE"

    # Follow-up flow
    COLLECT_STATUS = "COLLECT_STATUS"

    # Terminal states
    COMPLETED = "COMPLETED"
    REMINDER = "REMINDER"
    CLOSED = "CLOSED"


# State transition rules: which states can transition to which
STATE_TRANSITIONS: dict[ConversationState, list[ConversationState]] = {
    ConversationState.IDLE: [ConversationState.GREETING],
    ConversationState.GREETING: [
        ConversationState.INTENT_DETECTION,
        ConversationState.REMINDER,
    ],
    ConversationState.INTENT_DETECTION: [
        ConversationState.ASK_REASON,
        ConversationState.CONFIRM_EMERGENCY,
        ConversationState.COLLECT_STATUS,
        ConversationState.GREETING,
        ConversationState.REMINDER,
        ConversationState.CLOSED,
    ],
    ConversationState.ASK_REASON: [
        ConversationState.OFFER_SLOTS,
        ConversationState.CONFIRM_EMERGENCY,
        ConversationState.REMINDER,
    ],
    ConversationState.OFFER_SLOTS: [
        ConversationState.AWAIT_SELECTION,
        ConversationState.ASK_REASON,
        ConversationState.REMINDER,
    ],
    ConversationState.AWAIT_SELECTION: [
        ConversationState.CONFIRM_BOOKING,
        ConversationState.OFFER_SLOTS,
        ConversationState.REMINDER,
    ],
    ConversationState.CONFIRM_BOOKING: [
        ConversationState.COMPLETED,
        ConversationState.OFFER_SLOTS,
        ConversationState.REMINDER,
    ],
    ConversationState.CONFIRM_EMERGENCY: [
        ConversationState.ESCALATE,
        ConversationState.ASK_REASON,
        ConversationState.CLOSED,
    ],
    ConversationState.ESCALATE: [
        ConversationState.COMPLETED,
    ],
    ConversationState.COLLECT_STATUS: [
        ConversationState.COMPLETED,
        ConversationState.ESCALATE,
        ConversationState.REMINDER,
    ],
    ConversationState.COMPLETED: [
        ConversationState.CLOSED,
    ],
    ConversationState.REMINDER: [
        ConversationState.INTENT_DETECTION,
        ConversationState.CLOSED,
    ],
    ConversationState.CLOSED: [
        ConversationState.GREETING,  # New conversation can start
    ],
}


# Timeout configuration per state (in minutes)
STATE_TIMEOUTS: dict[ConversationState, int] = {
    ConversationState.GREETING: 5,
    ConversationState.INTENT_DETECTION: 10,
    ConversationState.ASK_REASON: 15,
    ConversationState.OFFER_SLOTS: 15,
    ConversationState.AWAIT_SELECTION: 15,
    ConversationState.CONFIRM_BOOKING: 10,
    ConversationState.CONFIRM_EMERGENCY: 5,
    ConversationState.COLLECT_STATUS: 60 * 24,  # 24 hours
    ConversationState.REMINDER: 60 * 24,  # 24 hours
}


def get_timeout_duration(state: ConversationState) -> Optional[timedelta]:
    """Get the timeout duration for a state."""
    minutes = STATE_TIMEOUTS.get(state)
    if minutes:
        return timedelta(minutes=minutes)
    return None


def can_transition(from_state: ConversationState, to_state: ConversationState) -> bool:
    """Check if a state transition is valid."""
    allowed = STATE_TRANSITIONS.get(from_state, [])
    return to_state in allowed


def is_terminal_state(state: ConversationState) -> bool:
    """Check if a state is terminal (conversation ended)."""
    return state in [ConversationState.CLOSED, ConversationState.COMPLETED]


def is_scheduling_state(state: ConversationState) -> bool:
    """Check if state is part of scheduling flow."""
    return state in [
        ConversationState.ASK_REASON,
        ConversationState.OFFER_SLOTS,
        ConversationState.AWAIT_SELECTION,
        ConversationState.CONFIRM_BOOKING,
    ]


def is_emergency_state(state: ConversationState) -> bool:
    """Check if state is part of emergency flow."""
    return state in [
        ConversationState.CONFIRM_EMERGENCY,
        ConversationState.ESCALATE,
    ]
