"""Calendar and scheduling service."""

from datetime import date, datetime, time, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import pytz

from app.models import Clinic, Appointment, Client, Pet, Staff
from app.schemas.appointment import TimeSlot, AppointmentCreate, BookingResult


class CalendarService:
    """Service for managing calendar and appointments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_clinic(self, clinic_id: UUID) -> Optional[Clinic]:
        """Get clinic by ID."""
        result = await self.db.execute(select(Clinic).where(Clinic.id == clinic_id))
        return result.scalar_one_or_none()

    async def get_working_hours(
        self, clinic_id: UUID, target_date: date
    ) -> Optional[dict]:
        """Get working hours for a specific date."""
        clinic = await self.get_clinic(clinic_id)
        if not clinic:
            return None

        day_name = target_date.strftime("%A").lower()
        hours = clinic.working_hours.get(day_name)

        if not hours:
            return None

        return hours

    def generate_time_slots(
        self,
        start_str: str,
        end_str: str,
        duration_minutes: int,
        interval_minutes: int = 15,
    ) -> list[TimeSlot]:
        """Generate all possible time slots within a range."""
        slots = []

        start_parts = start_str.split(":")
        end_parts = end_str.split(":")

        start_time = time(int(start_parts[0]), int(start_parts[1]))
        end_time = time(int(end_parts[0]), int(end_parts[1]))

        current = datetime.combine(date.today(), start_time)
        end_dt = datetime.combine(date.today(), end_time)

        duration = timedelta(minutes=duration_minutes)
        interval = timedelta(minutes=interval_minutes)

        while current + duration <= end_dt:
            slot_end = current + duration
            slots.append(
                TimeSlot(
                    start=current.strftime("%H:%M"),
                    end=slot_end.strftime("%H:%M"),
                )
            )
            current += interval

        return slots

    async def get_appointments_for_date(
        self,
        clinic_id: UUID,
        target_date: date,
        staff_id: Optional[UUID] = None,
        exclude_cancelled: bool = True,
    ) -> list[Appointment]:
        """Get all appointments for a specific date."""
        clinic = await self.get_clinic(clinic_id)
        if not clinic:
            return []

        tz = pytz.timezone(clinic.timezone)
        start_of_day = tz.localize(datetime.combine(target_date, time.min))
        end_of_day = tz.localize(datetime.combine(target_date, time.max))

        query = select(Appointment).where(
            and_(
                Appointment.clinic_id == clinic_id,
                Appointment.start_time >= start_of_day,
                Appointment.start_time <= end_of_day,
            )
        )

        if staff_id:
            query = query.where(Appointment.staff_id == staff_id)

        if exclude_cancelled:
            query = query.where(Appointment.status != "cancelled")

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def has_overlap(
        self, slot: TimeSlot, existing_appointments: list[Appointment], target_date: date
    ) -> bool:
        """Check if a slot overlaps with any existing appointment."""
        slot_start_parts = slot.start.split(":")
        slot_end_parts = slot.end.split(":")

        slot_start = datetime.combine(
            target_date, time(int(slot_start_parts[0]), int(slot_start_parts[1]))
        )
        slot_end = datetime.combine(
            target_date, time(int(slot_end_parts[0]), int(slot_end_parts[1]))
        )

        for apt in existing_appointments:
            # Make naive for comparison if needed
            apt_start = apt.start_time.replace(tzinfo=None) if apt.start_time.tzinfo else apt.start_time
            apt_end = apt.end_time.replace(tzinfo=None) if apt.end_time.tzinfo else apt.end_time

            if slot_start < apt_end and slot_end > apt_start:
                return True

        return False

    async def find_available_slots(
        self,
        clinic_id: UUID,
        target_date: date,
        duration_minutes: int = 30,
        staff_id: Optional[UUID] = None,
    ) -> list[TimeSlot]:
        """Find all available slots for a given date."""
        working_hours = await self.get_working_hours(clinic_id, target_date)

        if not working_hours:
            return []

        # Generate all possible slots
        possible_slots = self.generate_time_slots(
            start_str=working_hours["start"],
            end_str=working_hours["end"],
            duration_minutes=duration_minutes,
            interval_minutes=15,
        )

        # Get existing appointments
        existing = await self.get_appointments_for_date(
            clinic_id=clinic_id,
            target_date=target_date,
            staff_id=staff_id,
        )

        # Filter out occupied slots
        available = []
        for slot in possible_slots:
            if not self.has_overlap(slot, existing, target_date):
                available.append(slot)

        return available

    async def find_or_create_client(
        self,
        clinic_id: UUID,
        phone: str,
        name: Optional[str] = None,
    ) -> Client:
        """Find existing client or create new one."""
        result = await self.db.execute(
            select(Client).where(
                and_(Client.clinic_id == clinic_id, Client.phone == phone)
            )
        )
        client = result.scalar_one_or_none()

        if client:
            if name and not client.name:
                client.name = name
                await self.db.flush()
            return client

        client = Client(
            clinic_id=clinic_id,
            phone=phone,
            name=name,
        )
        self.db.add(client)
        await self.db.flush()
        return client

    async def find_or_create_pet(
        self,
        client_id: UUID,
        species: str,
        name: Optional[str] = None,
    ) -> Pet:
        """Find existing pet or create new one."""
        query = select(Pet).where(Pet.client_id == client_id)
        if name:
            query = query.where(Pet.name == name)
        else:
            query = query.where(Pet.species == species)

        result = await self.db.execute(query)
        pet = result.scalar_one_or_none()

        if pet:
            return pet

        pet = Pet(
            client_id=client_id,
            species=species,
            name=name,
        )
        self.db.add(pet)
        await self.db.flush()
        return pet

    def infer_appointment_type(self, reason: str) -> str:
        """Infer appointment type from reason text."""
        reason_lower = reason.lower()

        if any(word in reason_lower for word in ["vacuna", "vaccine", "vaccination"]):
            return "vaccination"
        elif any(
            word in reason_lower
            for word in ["emergencia", "urgente", "emergency", "urgent"]
        ):
            return "emergency"
        elif any(
            word in reason_lower
            for word in ["cirugía", "cirugia", "surgery", "operación", "operacion"]
        ):
            return "surgery"
        elif any(
            word in reason_lower
            for word in ["peluquería", "peluqueria", "grooming", "baño", "bano"]
        ):
            return "grooming"
        else:
            return "consultation"

    async def book_appointment(
        self,
        clinic_id: UUID,
        appointment_data: AppointmentCreate,
    ) -> BookingResult:
        """Atomically book an appointment."""
        clinic = await self.get_clinic(clinic_id)
        if not clinic:
            return BookingResult(success=False, error="CLINIC_NOT_FOUND")

        tz = pytz.timezone(clinic.timezone)

        # Determine appointment type and duration
        appointment_type = appointment_data.appointment_type or self.infer_appointment_type(
            appointment_data.reason
        )
        duration_minutes = clinic.appointment_duration_minutes.get(appointment_type, 30)

        # Calculate end time
        start_time = appointment_data.start_time
        if start_time.tzinfo is None:
            start_time = tz.localize(start_time)

        end_time = start_time + timedelta(minutes=duration_minutes)

        # Check for conflicts
        existing = await self.get_appointments_for_date(
            clinic_id=clinic_id,
            target_date=start_time.date(),
        )

        for apt in existing:
            if start_time < apt.end_time and end_time > apt.start_time:
                # Conflict found
                alternative_slots = await self.find_available_slots(
                    clinic_id=clinic_id,
                    target_date=start_time.date(),
                    duration_minutes=duration_minutes,
                )
                return BookingResult(
                    success=False,
                    error="SLOT_TAKEN",
                    alternative_slots=alternative_slots[:3],
                )

        # Create client
        client = await self.find_or_create_client(
            clinic_id=clinic_id,
            phone=appointment_data.client_phone,
            name=appointment_data.client_name,
        )

        # Create pet
        pet = await self.find_or_create_pet(
            client_id=client.id,
            species=appointment_data.pet_type,
            name=appointment_data.pet_name,
        )

        # Create appointment
        appointment = Appointment(
            clinic_id=clinic_id,
            client_id=client.id,
            pet_id=pet.id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            appointment_type=appointment_type,
            reason=appointment_data.reason,
            source=appointment_data.source,
            conversation_id=appointment_data.conversation_id,
            notes=appointment_data.notes,
        )

        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)

        # Generate confirmation message
        confirmation = self.generate_confirmation_message(
            appointment, pet, client, clinic
        )

        return BookingResult(
            success=True,
            appointment=None,  # Will be populated by the caller
            confirmation_message=confirmation,
        )

    def generate_confirmation_message(
        self,
        appointment: Appointment,
        pet: Pet,
        client: Client,
        clinic: Clinic,
    ) -> str:
        """Generate a confirmation message in Spanish."""
        tz = pytz.timezone(clinic.timezone)
        local_time = appointment.start_time.astimezone(tz)

        day_names = {
            0: "lunes",
            1: "martes",
            2: "miércoles",
            3: "jueves",
            4: "viernes",
            5: "sábado",
            6: "domingo",
        }
        month_names = {
            1: "enero",
            2: "febrero",
            3: "marzo",
            4: "abril",
            5: "mayo",
            6: "junio",
            7: "julio",
            8: "agosto",
            9: "septiembre",
            10: "octubre",
            11: "noviembre",
            12: "diciembre",
        }

        day_name = day_names[local_time.weekday()]
        month_name = month_names[local_time.month]
        time_str = local_time.strftime("%I:%M %p").lstrip("0")

        pet_name = pet.name or f"su {pet.species}"

        return (
            f"Cita confirmada para {pet_name} el {day_name} {local_time.day} de "
            f"{month_name} a las {time_str}."
        )

    async def get_next_available(
        self, clinic_id: UUID, duration_minutes: int = 30
    ) -> Optional[dict]:
        """Find the next available slot across upcoming days."""
        today = date.today()

        for days_ahead in range(14):  # Look up to 2 weeks ahead
            target_date = today + timedelta(days=days_ahead)
            slots = await self.find_available_slots(
                clinic_id=clinic_id,
                target_date=target_date,
                duration_minutes=duration_minutes,
            )

            if slots:
                return {
                    "date": target_date.isoformat(),
                    "time": slots[0].start,
                }

        return None
