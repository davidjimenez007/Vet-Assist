# VetAssist WhatsApp Automation - Technical Architecture

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   [WhatsApp Business API]  ←──webhook──→  [Twilio / 360dialog]             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INGRESS LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   [Webhook Handler]                                                         │
│   - Validates webhook signature                                             │
│   - Parses incoming message                                                 │
│   - Enqueues to processing queue                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONVERSATION ENGINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │  Conversation   │    │     Intent      │    │     State       │        │
│   │    Manager      │───▶│   Classifier    │───▶│    Router       │        │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                                              │                  │
│           │              ┌───────────────────────────────┼──────────┐       │
│           │              │                               │          │       │
│           ▼              ▼                               ▼          ▼       │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│   │  Greeting   │ │ Scheduling  │ │  Emergency  │ │  Follow-up  │          │
│   │   Agent     │ │   Agent     │ │   Agent     │ │   Agent     │          │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ACTION LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │    Calendar     │    │     Alert       │    │    Message      │        │
│   │    Service      │    │    Service      │    │    Sender       │        │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PostgreSQL                                                                │
│   - clinics, clients, pets                                                  │
│   - conversations, messages                                                 │
│   - appointments                                                            │
│   - emergency_events                                                        │
│   - follow_up_logs                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Conversation State Machine

### 2.1 States

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         CONVERSATION STATES                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  IDLE ──────────────────▶ GREETING                                       │
│                               │                                          │
│                               ▼                                          │
│                        INTENT_DETECTION                                  │
│                          │    │    │                                     │
│            ┌─────────────┘    │    └─────────────┐                       │
│            ▼                  ▼                  ▼                       │
│     SCHEDULING_FLOW    EMERGENCY_FLOW    FOLLOWUP_RESPONSE              │
│            │                  │                  │                       │
│            ▼                  ▼                  ▼                       │
│     ┌──────────┐       ┌──────────┐       ┌──────────┐                  │
│     │ ASK_     │       │ CONFIRM_ │       │ COLLECT_ │                  │
│     │ REASON   │       │ EMERGENCY│       │ STATUS   │                  │
│     └────┬─────┘       └────┬─────┘       └────┬─────┘                  │
│          ▼                  │                  │                         │
│     ┌──────────┐            │                  │                         │
│     │ OFFER_   │            ▼                  │                         │
│     │ SLOTS    │       ┌──────────┐            │                         │
│     └────┬─────┘       │ ESCALATE │            │                         │
│          ▼             └────┬─────┘            │                         │
│     ┌──────────┐            │                  │                         │
│     │ AWAIT_   │            │                  │                         │
│     │ SELECTION│            │                  │                         │
│     └────┬─────┘            │                  │                         │
│          ▼                  │                  │                         │
│     ┌──────────┐            │                  │                         │
│     │ CONFIRM_ │            │                  │                         │
│     │ BOOKING  │            │                  │                         │
│     └────┬─────┘            │                  │                         │
│          │                  │                  │                         │
│          └──────────────────┴──────────────────┘                         │
│                             │                                            │
│                             ▼                                            │
│                        COMPLETED                                         │
│                             │                                            │
│                             ▼                                            │
│                          CLOSED                                          │
│                                                                          │
│  TIMEOUT paths:                                                          │
│  - Any state → REMINDER (after 30 min)                                   │
│  - REMINDER → CLOSED (after 24 hours)                                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 State Definitions

| State | Description | Timeout | Fallback |
|-------|-------------|---------|----------|
| `IDLE` | No active conversation | - | - |
| `GREETING` | Initial contact, identify client | 5 min | INTENT_DETECTION |
| `INTENT_DETECTION` | Classify user intent | 10 min | REMINDER |
| `ASK_REASON` | Collect consultation reason | 15 min | REMINDER |
| `OFFER_SLOTS` | Present available times | 15 min | REMINDER |
| `AWAIT_SELECTION` | Wait for slot choice | 15 min | REMINDER |
| `CONFIRM_BOOKING` | Final confirmation | 10 min | REMINDER |
| `CONFIRM_EMERGENCY` | Verify emergency is real | 5 min | CLOSE |
| `ESCALATE` | Alert sent, awaiting vet | - | - |
| `COLLECT_STATUS` | Follow-up response collection | 24 hr | CLOSE |
| `COMPLETED` | Action completed | - | CLOSE |
| `REMINDER` | Inactivity reminder sent | 24 hr | CLOSE |
| `CLOSED` | Conversation ended | - | - |

### 2.3 State Transitions

```python
STATE_TRANSITIONS = {
    "IDLE": ["GREETING"],
    "GREETING": ["INTENT_DETECTION", "REMINDER"],
    "INTENT_DETECTION": ["ASK_REASON", "CONFIRM_EMERGENCY", "COLLECT_STATUS", "GREETING", "REMINDER"],
    "ASK_REASON": ["OFFER_SLOTS", "CONFIRM_EMERGENCY", "REMINDER"],
    "OFFER_SLOTS": ["AWAIT_SELECTION", "ASK_REASON", "REMINDER"],
    "AWAIT_SELECTION": ["CONFIRM_BOOKING", "OFFER_SLOTS", "REMINDER"],
    "CONFIRM_BOOKING": ["COMPLETED", "OFFER_SLOTS", "REMINDER"],
    "CONFIRM_EMERGENCY": ["ESCALATE", "ASK_REASON", "CLOSED"],
    "ESCALATE": ["COMPLETED"],
    "COLLECT_STATUS": ["COMPLETED", "ESCALATE", "REMINDER"],
    "COMPLETED": ["CLOSED"],
    "REMINDER": ["INTENT_DETECTION", "CLOSED"],
    "CLOSED": ["GREETING"],  # New conversation can start
}
```

---

## 3. WhatsApp Conversation Examples

### 3.1 Appointment Scheduling (Happy Path)

```
CLIENTE: Hola, necesito una cita para mi perro
    [STATE: IDLE → GREETING → INTENT_DETECTION → ASK_REASON]

SISTEMA: Hola, bienvenido a [Clínica]. Con gusto te ayudo a agendar.
         ¿Cuál es el motivo de la consulta?
    [STATE: ASK_REASON]

CLIENTE: Le salió una bolita en el cuello y quiero que la revisen
    [STATE: ASK_REASON → OFFER_SLOTS]

SISTEMA: Entendido, revisión de masa en cuello.
         Tengo disponibilidad:

         1. Hoy 4:30 PM
         2. Mañana 9:00 AM
         3. Mañana 2:00 PM

         ¿Cuál te funciona mejor?
    [STATE: OFFER_SLOTS]

CLIENTE: Mañana a las 9
    [STATE: OFFER_SLOTS → AWAIT_SELECTION → CONFIRM_BOOKING]

SISTEMA: Perfecto. Confirmo tu cita:

         📅 Viernes 31 de enero
         🕘 9:00 AM
         🐕 Revisión de masa en cuello

         ¿Confirmas esta cita? (Sí/No)
    [STATE: CONFIRM_BOOKING]

CLIENTE: Sí
    [STATE: CONFIRM_BOOKING → COMPLETED]

SISTEMA: ✓ Cita confirmada.

         Te esperamos mañana a las 9:00 AM.
         Si necesitas cancelar o cambiar, escríbenos con tiempo.
    [STATE: COMPLETED → CLOSED]
```

**Total: 6 mensajes del sistema**

### 3.2 Emergency Flow

```
CLIENTE: Mi gato se comió veneno para ratas ayuda!!!
    [STATE: IDLE → GREETING → INTENT_DETECTION → CONFIRM_EMERGENCY]
    [EMERGENCY KEYWORDS DETECTED: "veneno", "ayuda"]

SISTEMA: Entiendo que es una emergencia.
         Para confirmar: ¿la vida de tu mascota está en riesgo en este momento?

         Responde SÍ o NO
    [STATE: CONFIRM_EMERGENCY]

CLIENTE: SÍ
    [STATE: CONFIRM_EMERGENCY → ESCALATE]
    [ACTION: Create priority slot, Alert veterinarian]

SISTEMA: 🚨 EMERGENCIA REGISTRADA

         El veterinario ha sido notificado y te contactará en los próximos minutos.

         Mientras tanto:
         - No induzcas el vómito
         - Mantén a tu mascota tranquila
         - Ten a la mano el empaque del producto

         ¿En qué dirección te encuentras para indicarte cómo llegar a la clínica?
    [STATE: ESCALATE]

    [ALERT SENT TO VET: "🚨 EMERGENCIA: Intoxicación por rodenticida - Gato - [Teléfono cliente]"]
```

### 3.3 Follow-up Response

```
    [SYSTEM INITIATES - 24 hours post-surgery]

SISTEMA: Hola, soy el asistente de [Clínica].
         ¿Cómo sigue Luna después de la cirugía de ayer?
    [STATE: IDLE → COLLECT_STATUS]

CLIENTE: Bien, está comiendo normal pero se queja cuando camina
    [STATE: COLLECT_STATUS]
    [ANALYSIS: "se queja cuando camina" = potential concern]

SISTEMA: Gracias por la información.
         Es normal algo de molestia los primeros días.

         ¿El quejido es constante o solo al hacer ciertos movimientos?
    [STATE: COLLECT_STATUS - gathering more info]

CLIENTE: Solo cuando salta o baja escaleras
    [STATE: COLLECT_STATUS → COMPLETED]
    [ANALYSIS: Expected post-op behavior, no escalation needed]

SISTEMA: Eso es normal durante la recuperación.
         Evita que salte o suba escaleras los próximos 5 días.

         Si notas sangrado, inflamación excesiva o deja de comer, escríbenos de inmediato.

         Te escribo mañana para saber cómo sigue. 🐾
    [STATE: COMPLETED → CLOSED]
    [ACTION: Schedule next follow-up in 24 hours]
```

### 3.4 Unclear Intent / Redirect

```
CLIENTE: Hola cuanto cuesta una vacuna
    [STATE: IDLE → GREETING → INTENT_DETECTION]
    [INTENT: price_inquiry - not in scope]

SISTEMA: Hola, gracias por escribir.
         Para información sobre precios, te recomiendo llamar directamente al consultorio: [número].

         ¿Hay algo más en lo que pueda ayudarte? Por ejemplo, ¿necesitas agendar una cita?
    [STATE: INTENT_DETECTION - redirect to booking]

CLIENTE: Sí, quiero vacunar a mi perro
    [STATE: INTENT_DETECTION → ASK_REASON]

SISTEMA: Con gusto te ayudo a agendar.
         ¿Qué vacuna necesita? (Ej: rabia, múltiple, desparasitación)
    [Continues normal flow...]
```

### 3.5 Timeout Handling

```
CLIENTE: Hola necesito una cita
    [STATE: IDLE → GREETING → INTENT_DETECTION → ASK_REASON]

SISTEMA: Hola, con gusto te ayudo. ¿Cuál es el motivo de la consulta?
    [STATE: ASK_REASON]

    [30 MINUTES PASS - NO RESPONSE]
    [STATE: ASK_REASON → REMINDER]

SISTEMA: Hola, ¿sigues ahí?
         Quedamos pendientes de agendar tu cita. ¿En qué te puedo ayudar?
    [STATE: REMINDER]

    [24 HOURS PASS - NO RESPONSE]
    [STATE: REMINDER → CLOSED]

    [No message sent - conversation silently closed]
```

---

## 4. Scheduling Logic

### 4.1 Slot Generation

```python
def get_available_slots(clinic_id: str, date: date, duration: int = 30) -> list[TimeSlot]:
    """
    Returns available appointment slots for a given date.

    Rules:
    - Respects clinic business hours
    - Excludes existing appointments
    - Excludes blocked times
    - Adds buffer between appointments (5 min)
    - Returns max 10 slots per query
    """

    # Get clinic configuration
    clinic = get_clinic(clinic_id)
    day_of_week = date.weekday()
    hours = clinic.business_hours.get(day_of_week)

    if not hours or not hours.is_open:
        return []

    # Generate all possible slots
    slot_start = datetime.combine(date, hours.open_time)
    slot_end = datetime.combine(date, hours.close_time)

    all_slots = []
    current = slot_start

    while current + timedelta(minutes=duration) <= slot_end:
        all_slots.append(TimeSlot(
            start=current,
            end=current + timedelta(minutes=duration)
        ))
        current += timedelta(minutes=30)  # 30-min intervals

    # Get existing appointments
    existing = get_appointments_for_date(clinic_id, date)

    # Filter out conflicts
    available = []
    for slot in all_slots:
        buffer_start = slot.start - timedelta(minutes=5)
        buffer_end = slot.end + timedelta(minutes=5)

        has_conflict = any(
            apt.start_time < buffer_end and apt.end_time > buffer_start
            for apt in existing
            if apt.status not in ['cancelled']
        )

        if not has_conflict:
            available.append(slot)

    return available[:10]
```

### 4.2 Appointment Creation

```python
def create_appointment_from_conversation(
    conversation_id: str,
    slot: TimeSlot,
    reason: str
) -> Appointment:
    """
    Creates an appointment from a WhatsApp conversation.

    Steps:
    1. Validate slot is still available (double-check)
    2. Get or create client from phone number
    3. Get or create pet (if identified)
    4. Create appointment
    5. Log to conversation
    6. Return confirmation
    """

    conversation = get_conversation(conversation_id)

    # Race condition check
    if not is_slot_available(conversation.clinic_id, slot):
        raise SlotNoLongerAvailable()

    # Get or create client
    client = get_or_create_client(
        clinic_id=conversation.clinic_id,
        phone=conversation.client_phone,
        name=conversation.extracted_client_name
    )

    # Get or create pet if identified
    pet = None
    if conversation.extracted_pet_name:
        pet = get_or_create_pet(
            client_id=client.id,
            name=conversation.extracted_pet_name,
            species=conversation.extracted_pet_species
        )

    # Create appointment
    appointment = Appointment(
        id=uuid4(),
        clinic_id=conversation.clinic_id,
        client_id=client.id,
        pet_id=pet.id if pet else None,
        start_time=slot.start,
        end_time=slot.end,
        duration_minutes=(slot.end - slot.start).minutes,
        reason=reason,
        status='scheduled',
        source='whatsapp',
        conversation_id=conversation_id,
        priority='normal',
        created_at=datetime.utcnow()
    )

    db.add(appointment)
    db.commit()

    # Log action
    log_conversation_action(
        conversation_id=conversation_id,
        action='appointment_created',
        data={'appointment_id': str(appointment.id)}
    )

    return appointment
```

### 4.3 Slot Selection Parser

```python
def parse_slot_selection(user_message: str, offered_slots: list[TimeSlot]) -> TimeSlot | None:
    """
    Parses user's slot selection from free text.

    Handles:
    - "1", "la primera", "opción 1"
    - "mañana a las 9"
    - "la de las 2 de la tarde"
    - "el viernes"
    """

    message = user_message.lower().strip()

    # Direct number selection
    number_patterns = [
        (r'^1$|primera|opción 1|uno', 0),
        (r'^2$|segunda|opción 2|dos', 1),
        (r'^3$|tercera|opción 3|tres', 2),
    ]

    for pattern, index in number_patterns:
        if re.search(pattern, message):
            if index < len(offered_slots):
                return offered_slots[index]

    # Time-based selection
    time_patterns = [
        (r'(\d{1,2})\s*(am|pm|de la mañana|de la tarde)', extract_time),
        (r'mañana|hoy|viernes|lunes|...', extract_relative_date),
    ]

    for pattern, extractor in time_patterns:
        match = re.search(pattern, message)
        if match:
            target = extractor(match)
            for slot in offered_slots:
                if slot_matches(slot, target):
                    return slot

    return None  # Could not parse
```

---

## 5. Emergency Escalation Logic

### 5.1 Emergency Detection

```python
EMERGENCY_KEYWORDS = {
    'high': [
        'veneno', 'envenenado', 'envenenamiento',
        'atropellado', 'atropelló', 'carro',
        'no respira', 'no puede respirar', 'asfixia',
        'convulsión', 'convulsionando', 'convulsiones',
        'sangre', 'sangrando', 'hemorragia',
        'no se mueve', 'inconsciente', 'desmayado',
        'parto', 'dando a luz', 'no puede parir'
    ],
    'medium': [
        'urgente', 'emergencia', 'ayuda',
        'muy mal', 'grave', 'crítico',
        'vomitando sangre', 'diarrea con sangre',
        'hinchado', 'inflamado'
    ]
}

def detect_emergency(message: str) -> EmergencyDetection:
    """
    Detects potential emergency from message content.
    Returns confidence level and matched keywords.
    """

    message_lower = message.lower()

    high_matches = [kw for kw in EMERGENCY_KEYWORDS['high'] if kw in message_lower]
    medium_matches = [kw for kw in EMERGENCY_KEYWORDS['medium'] if kw in message_lower]

    if high_matches:
        return EmergencyDetection(
            is_potential_emergency=True,
            confidence='high',
            matched_keywords=high_matches,
            requires_confirmation=True
        )

    if len(medium_matches) >= 2 or (medium_matches and '!' in message):
        return EmergencyDetection(
            is_potential_emergency=True,
            confidence='medium',
            matched_keywords=medium_matches,
            requires_confirmation=True
        )

    return EmergencyDetection(is_potential_emergency=False)
```

### 5.2 Emergency Confirmation & Escalation

```python
def handle_emergency_confirmation(
    conversation_id: str,
    user_confirmed: bool
) -> EmergencyAction:
    """
    Handles user's response to emergency confirmation.
    """

    conversation = get_conversation(conversation_id)
    client = get_client_by_phone(conversation.client_phone)

    # Check for abuse
    if client and client.false_emergency_count >= 1:
        return EmergencyAction(
            action='denied',
            message='Lo siento, el acceso a emergencias está restringido para este número. Por favor llama directamente al consultorio.'
        )

    if not user_confirmed:
        # Log false alarm
        if client:
            client.false_emergency_count += 1
            db.commit()

        return EmergencyAction(
            action='redirect_to_scheduling',
            message='Entendido. ¿Te gustaría agendar una cita regular para revisión?'
        )

    # CONFIRMED EMERGENCY
    return execute_emergency_escalation(conversation_id)


def execute_emergency_escalation(conversation_id: str) -> EmergencyAction:
    """
    Executes full emergency escalation protocol.
    """

    conversation = get_conversation(conversation_id)
    clinic = get_clinic(conversation.clinic_id)

    # 1. Create emergency event
    emergency = EmergencyEvent(
        id=uuid4(),
        clinic_id=conversation.clinic_id,
        conversation_id=conversation_id,
        client_phone=conversation.client_phone,
        description=conversation.emergency_description,
        keywords_detected=conversation.emergency_keywords,
        status='active',
        created_at=datetime.utcnow()
    )
    db.add(emergency)

    # 2. Create priority appointment slot
    priority_slot = create_emergency_slot(
        clinic_id=conversation.clinic_id,
        emergency_id=emergency.id
    )

    # 3. Alert veterinarian(s)
    escalation_contacts = get_escalation_contacts(conversation.clinic_id)

    for contact in escalation_contacts:
        send_emergency_alert(
            phone=contact.phone,
            message=format_emergency_alert(emergency, conversation)
        )

        # Log alert
        EmergencyAlert(
            emergency_id=emergency.id,
            contact_phone=contact.phone,
            sent_at=datetime.utcnow(),
            status='sent'
        )

    # 4. Update conversation state
    conversation.state = 'ESCALATE'
    conversation.emergency_id = emergency.id
    db.commit()

    return EmergencyAction(
        action='escalated',
        emergency_id=emergency.id,
        message=format_emergency_client_response(clinic)
    )


def format_emergency_alert(emergency: EmergencyEvent, conversation: Conversation) -> str:
    """Formats alert message for veterinarian."""

    return f"""🚨 EMERGENCIA

📞 {conversation.client_phone}
🐾 {conversation.extracted_pet_species or 'Mascota'}
⚠️ {emergency.description[:100]}

Palabras clave: {', '.join(emergency.keywords_detected[:3])}

Responde a este mensaje para confirmar recepción."""
```

### 5.3 Emergency Slot Creation

```python
def create_emergency_slot(clinic_id: str, emergency_id: str) -> Appointment:
    """
    Creates an emergency appointment slot.

    Rules:
    - Overrides normal schedule
    - Does NOT cancel existing appointments
    - Creates a parallel priority slot
    - Marked as emergency for dashboard visibility
    """

    now = datetime.utcnow()

    # Emergency slot starts now, 60 min duration
    appointment = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        start_time=now,
        end_time=now + timedelta(minutes=60),
        duration_minutes=60,
        reason='EMERGENCIA',
        status='emergency',
        source='whatsapp',
        priority='emergency',
        emergency_id=emergency_id,
        created_at=now
    )

    db.add(appointment)
    db.commit()

    return appointment
```

---

## 6. Follow-up Automation Logic

### 6.1 Follow-up Protocol Definition

```python
# Default follow-up protocols by procedure type
FOLLOW_UP_PROTOCOLS = {
    'surgery': {
        'schedule': [24, 48, 72, 168],  # hours after procedure
        'messages': [
            "Hola, ¿cómo sigue {pet_name} después de la cirugía de ayer? ¿Ha comido y orinado con normalidad?",
            "Hola, segundo día post-operatorio. ¿Cómo va la recuperación de {pet_name}? ¿Alguna molestia o sangrado?",
            "Hola, ¿cómo sigue {pet_name}? ¿La herida se ve bien? ¿Ha tenido fiebre o dejado de comer?",
            "Hola, esta semana toca revisión de puntos para {pet_name}. ¿Quieres que agendemos la cita?"
        ],
        'escalation_keywords': ['sangre', 'sangrado', 'fiebre', 'no come', 'hinchado', 'pus', 'olor']
    },
    'vaccination': {
        'schedule': [24],
        'messages': [
            "Hola, ¿cómo está {pet_name} después de la vacuna? Es normal algo de decaimiento. Si presenta vómito, diarrea o hinchazón en la cara, escríbenos de inmediato."
        ],
        'escalation_keywords': ['vómito', 'diarrea', 'hinchazón', 'cara hinchada', 'no respira']
    },
    'consultation': {
        'schedule': [48],
        'messages': [
            "Hola, ¿cómo sigue {pet_name}? ¿Ha mejorado con el tratamiento?"
        ],
        'escalation_keywords': ['peor', 'empeora', 'no mejora', 'igual']
    }
}
```

### 6.2 Follow-up Scheduler

```python
def schedule_follow_ups(appointment_id: str, procedure_type: str) -> list[FollowUp]:
    """
    Schedules follow-up messages after an appointment is completed.
    Called when appointment status changes to 'completed'.
    """

    appointment = get_appointment(appointment_id)
    protocol = FOLLOW_UP_PROTOCOLS.get(procedure_type, FOLLOW_UP_PROTOCOLS['consultation'])

    follow_ups = []

    for i, hours in enumerate(protocol['schedule']):
        scheduled_at = appointment.end_time + timedelta(hours=hours)

        follow_up = FollowUp(
            id=uuid4(),
            appointment_id=appointment_id,
            clinic_id=appointment.clinic_id,
            client_id=appointment.client_id,
            pet_id=appointment.pet_id,
            message_template=protocol['messages'][i],
            escalation_keywords=protocol['escalation_keywords'],
            scheduled_at=scheduled_at,
            status='pending',
            sequence_number=i + 1,
            created_at=datetime.utcnow()
        )

        db.add(follow_up)
        follow_ups.append(follow_up)

    db.commit()
    return follow_ups
```

### 6.3 Follow-up Processor

```python
async def process_pending_follow_ups():
    """
    Cron job that runs every 5 minutes.
    Sends pending follow-up messages.
    """

    now = datetime.utcnow()

    pending = db.query(FollowUp).filter(
        FollowUp.status == 'pending',
        FollowUp.scheduled_at <= now
    ).all()

    for follow_up in pending:
        try:
            await send_follow_up(follow_up)
            follow_up.status = 'sent'
            follow_up.sent_at = now
        except Exception as e:
            follow_up.status = 'failed'
            follow_up.error = str(e)

        db.commit()


async def send_follow_up(follow_up: FollowUp):
    """Sends a single follow-up message."""

    client = get_client(follow_up.client_id)
    pet = get_pet(follow_up.pet_id) if follow_up.pet_id else None

    # Format message
    message = follow_up.message_template.format(
        pet_name=pet.name if pet else 'tu mascota',
        client_name=client.name or ''
    )

    # Create conversation for follow-up
    conversation = Conversation(
        id=uuid4(),
        clinic_id=follow_up.clinic_id,
        client_phone=client.phone,
        channel='whatsapp',
        type='follow_up',
        follow_up_id=follow_up.id,
        state='COLLECT_STATUS',
        started_at=datetime.utcnow()
    )
    db.add(conversation)

    # Send via WhatsApp
    await whatsapp_send(
        phone=client.phone,
        message=message
    )

    # Log message
    Message(
        conversation_id=conversation.id,
        direction='outbound',
        content=message,
        sent_at=datetime.utcnow()
    )

    db.commit()
```

### 6.4 Follow-up Response Analysis

```python
def analyze_follow_up_response(
    follow_up_id: str,
    response_message: str
) -> FollowUpAnalysis:
    """
    Analyzes client's response to follow-up message.
    Determines if escalation is needed.
    """

    follow_up = get_follow_up(follow_up_id)
    message_lower = response_message.lower()

    # Check for escalation keywords
    matched_keywords = [
        kw for kw in follow_up.escalation_keywords
        if kw in message_lower
    ]

    # Sentiment analysis (simple)
    negative_indicators = ['mal', 'peor', 'preocupa', 'no mejora', 'problema']
    positive_indicators = ['bien', 'mejor', 'normal', 'tranquilo', 'comiendo']

    negative_count = sum(1 for ind in negative_indicators if ind in message_lower)
    positive_count = sum(1 for ind in positive_indicators if ind in message_lower)

    if matched_keywords or negative_count > positive_count:
        return FollowUpAnalysis(
            status='concern',
            requires_escalation=len(matched_keywords) > 0,
            matched_keywords=matched_keywords,
            recommendation='alert_vet' if matched_keywords else 'monitor'
        )

    return FollowUpAnalysis(
        status='normal',
        requires_escalation=False,
        recommendation='continue_protocol'
    )
```

---

## 7. MVP Boundaries

### 7.1 IN SCOPE (Layer 1)

| Feature | Status | Priority |
|---------|--------|----------|
| WhatsApp message reception | ✅ Build | P0 |
| Conversation state machine | ✅ Build | P0 |
| Intent classification | ✅ Build | P0 |
| Appointment scheduling | ✅ Build | P0 |
| Calendar integration | ✅ Build | P0 |
| Emergency detection | ✅ Build | P0 |
| Emergency confirmation | ✅ Build | P0 |
| Emergency escalation (alerts) | ✅ Build | P0 |
| Follow-up scheduling | ✅ Build | P1 |
| Follow-up message sending | ✅ Build | P1 |
| Follow-up response analysis | ✅ Build | P1 |
| Timeout handling | ✅ Build | P0 |
| Client/Pet auto-creation | ✅ Build | P0 |
| Dashboard: WhatsApp activity | ✅ Build | P1 |
| Dashboard: Emergency alerts | ✅ Build | P0 |

### 7.2 OUT OF SCOPE (Future Layers)

| Feature | Layer | Reason |
|---------|-------|--------|
| Medical records | Layer 2 | Different domain |
| Clinical notes | Layer 2 | Requires vet input |
| Prescriptions | Layer 2 | Medical decision |
| Lab results | Layer 2 | Medical data |
| Medical image analysis | Layer 3 | AI complexity |
| Diagnosis suggestions | Layer 3 | Liability |
| Payment processing | Layer 2 | Different integration |
| Inventory management | Layer 2 | Different domain |
| Multi-clinic support | Layer 2 | Scale complexity |
| Voice calls (Twilio Voice) | Layer 2 | Different channel |

### 7.3 Technical Debt Accepted for MVP

1. **Single LLM provider** - Claude only, no fallback
2. **Simple intent classification** - Keyword + LLM, no ML model
3. **Basic slot parsing** - Regex + LLM, not NLU
4. **No conversation recovery** - If state corrupted, restart
5. **Single timezone** - Colombia only (America/Bogota)
6. **Spanish only** - No multi-language support
7. **No message templates** - No WhatsApp Business template messages yet

---

## 8. Database Schema Extensions

```sql
-- Conversation state tracking
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS
    state VARCHAR(50) DEFAULT 'IDLE',
    state_data JSONB DEFAULT '{}',
    last_state_change TIMESTAMP,
    timeout_at TIMESTAMP,
    type VARCHAR(20) DEFAULT 'inbound',  -- inbound, follow_up
    follow_up_id UUID REFERENCES follow_ups(id);

-- Emergency events
CREATE TABLE IF NOT EXISTS emergency_events (
    id UUID PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    conversation_id UUID REFERENCES conversations(id),
    client_phone VARCHAR(20) NOT NULL,
    description TEXT,
    keywords_detected TEXT[],
    status VARCHAR(20) DEFAULT 'active',  -- active, resolved, false_alarm
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES staff(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Emergency alerts sent
CREATE TABLE IF NOT EXISTS emergency_alerts (
    id UUID PRIMARY KEY,
    emergency_id UUID NOT NULL REFERENCES emergency_events(id),
    contact_phone VARCHAR(20) NOT NULL,
    contact_name VARCHAR(100),
    sent_at TIMESTAMP DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'sent'  -- sent, delivered, acknowledged
);

-- Follow-up scheduling
CREATE TABLE IF NOT EXISTS follow_ups (
    id UUID PRIMARY KEY,
    appointment_id UUID NOT NULL REFERENCES appointments(id),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    client_id UUID NOT NULL REFERENCES clients(id),
    pet_id UUID REFERENCES pets(id),
    message_template TEXT NOT NULL,
    escalation_keywords TEXT[],
    scheduled_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, sent, responded, escalated, cancelled
    sequence_number INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Follow-up responses
CREATE TABLE IF NOT EXISTS follow_up_responses (
    id UUID PRIMARY KEY,
    follow_up_id UUID NOT NULL REFERENCES follow_ups(id),
    conversation_id UUID REFERENCES conversations(id),
    response_text TEXT,
    analysis_result JSONB,
    requires_escalation BOOLEAN DEFAULT FALSE,
    escalated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Client emergency abuse tracking
ALTER TABLE clients ADD COLUMN IF NOT EXISTS
    false_emergency_count INT DEFAULT 0,
    emergency_access_revoked BOOLEAN DEFAULT FALSE;

-- Indexes
CREATE INDEX idx_conversations_state ON conversations(clinic_id, state);
CREATE INDEX idx_conversations_timeout ON conversations(timeout_at) WHERE state != 'CLOSED';
CREATE INDEX idx_follow_ups_pending ON follow_ups(scheduled_at) WHERE status = 'pending';
CREATE INDEX idx_emergency_events_active ON emergency_events(clinic_id, status) WHERE status = 'active';
```

---

## 9. API Endpoints Required

### 9.1 WhatsApp Webhook

```
POST /webhooks/whatsapp
- Receives incoming WhatsApp messages
- Validates signature
- Processes message through conversation engine
```

### 9.2 Internal APIs

```
# Conversations
GET  /api/v1/conversations
GET  /api/v1/conversations/{id}
GET  /api/v1/conversations/{id}/messages

# Emergency
GET  /api/v1/emergencies
GET  /api/v1/emergencies/{id}
POST /api/v1/emergencies/{id}/resolve
POST /api/v1/emergencies/{id}/acknowledge

# Follow-ups
GET  /api/v1/follow-ups
GET  /api/v1/follow-ups/{id}
POST /api/v1/follow-ups/{id}/cancel

# Dashboard Stats
GET  /api/v1/analytics/whatsapp-activity
GET  /api/v1/analytics/emergency-summary
```

---

## 10. Implementation Order

### Phase 1: Core Engine (Week 1-2)
1. Conversation state machine
2. WhatsApp webhook handler
3. Basic intent classification
4. Greeting and redirect flows

### Phase 2: Scheduling (Week 2-3)
1. Slot generation
2. Slot selection parsing
3. Appointment creation from conversation
4. Confirmation flow

### Phase 3: Emergency (Week 3-4)
1. Emergency detection
2. Confirmation flow
3. Escalation alerts
4. Dashboard emergency view

### Phase 4: Follow-ups (Week 4-5)
1. Protocol configuration
2. Scheduler
3. Response analysis
4. Escalation from follow-up

### Phase 5: Polish (Week 5-6)
1. Timeout handling
2. Edge cases
3. Dashboard integration
4. Testing with real conversations
