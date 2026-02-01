"""Client and pet management endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.client import Client, Pet
from app.models.appointment import Appointment
from app.api.deps import CurrentClinic, DBSession

router = APIRouter()


# --- Schemas ---

class PetResponse(BaseModel):
    id: UUID
    name: Optional[str] = None
    species: str
    breed: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ClientResponse(BaseModel):
    id: UUID
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: str
    pets: list[PetResponse] = []
    appointment_count: int = 0

    class Config:
        from_attributes = True


class ClientCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class PetCreate(BaseModel):
    name: Optional[str] = None
    species: str
    breed: Optional[str] = None
    notes: Optional[str] = None


class PetUpdate(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    notes: Optional[str] = None


# --- Endpoints ---

@router.get("", response_model=list[ClientResponse])
async def list_clients(
    current_clinic: CurrentClinic,
    db: DBSession,
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
):
    """List clients with their pets."""
    query = (
        select(Client)
        .where(Client.clinic_id == current_clinic.id)
        .options(selectinload(Client.pets))
    )

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Client.name.ilike(search_term)) | (Client.phone.ilike(search_term))
        )

    query = query.order_by(Client.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    clients = result.scalars().all()

    # Get appointment counts
    responses = []
    for client in clients:
        count_result = await db.execute(
            select(func.count(Appointment.id)).where(Appointment.client_id == client.id)
        )
        apt_count = count_result.scalar() or 0

        responses.append(ClientResponse(
            id=client.id,
            phone=client.phone,
            name=client.name,
            email=client.email,
            created_at=client.created_at.isoformat(),
            pets=[PetResponse(
                id=p.id, name=p.name, species=p.species, breed=p.breed, notes=p.notes
            ) for p in client.pets],
            appointment_count=apt_count,
        ))

    return responses


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Create a new client."""
    # Check for duplicate phone
    existing = await db.execute(
        select(Client).where(
            Client.clinic_id == current_clinic.id,
            Client.phone == data.phone,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese telefono")

    client = Client(
        clinic_id=current_clinic.id,
        phone=data.phone,
        name=data.name,
        email=data.email,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)

    return ClientResponse(
        id=client.id,
        phone=client.phone,
        name=client.name,
        email=client.email,
        created_at=client.created_at.isoformat(),
        pets=[],
        appointment_count=0,
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Get a specific client."""
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id, Client.clinic_id == current_clinic.id)
        .options(selectinload(Client.pets))
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    count_result = await db.execute(
        select(func.count(Appointment.id)).where(Appointment.client_id == client.id)
    )
    apt_count = count_result.scalar() or 0

    return ClientResponse(
        id=client.id,
        phone=client.phone,
        name=client.name,
        email=client.email,
        created_at=client.created_at.isoformat(),
        pets=[PetResponse(
            id=p.id, name=p.name, species=p.species, breed=p.breed, notes=p.notes
        ) for p in client.pets],
        appointment_count=apt_count,
    )


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    update_data: ClientUpdate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Update a client."""
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id, Client.clinic_id == current_clinic.id)
        .options(selectinload(Client.pets))
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    count_result = await db.execute(
        select(func.count(Appointment.id)).where(Appointment.client_id == client.id)
    )
    apt_count = count_result.scalar() or 0

    return ClientResponse(
        id=client.id,
        phone=client.phone,
        name=client.name,
        email=client.email,
        created_at=client.created_at.isoformat(),
        pets=[PetResponse(
            id=p.id, name=p.name, species=p.species, breed=p.breed, notes=p.notes
        ) for p in client.pets],
        appointment_count=apt_count,
    )


# --- Pet endpoints ---

@router.post("/{client_id}/pets", response_model=PetResponse, status_code=201)
async def create_pet(
    client_id: UUID,
    data: PetCreate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Add a pet to a client."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.clinic_id == current_clinic.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    pet = Pet(
        client_id=client_id,
        name=data.name,
        species=data.species,
        breed=data.breed,
        notes=data.notes,
    )
    db.add(pet)
    await db.commit()
    await db.refresh(pet)

    return PetResponse(id=pet.id, name=pet.name, species=pet.species, breed=pet.breed, notes=pet.notes)


@router.patch("/{client_id}/pets/{pet_id}", response_model=PetResponse)
async def update_pet(
    client_id: UUID,
    pet_id: UUID,
    update_data: PetUpdate,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Update a pet."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.clinic_id == current_clinic.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    pet_result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.client_id == client_id)
    )
    pet = pet_result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(pet, field, value)

    await db.commit()
    await db.refresh(pet)

    return PetResponse(id=pet.id, name=pet.name, species=pet.species, breed=pet.breed, notes=pet.notes)


@router.delete("/{client_id}/pets/{pet_id}", status_code=204)
async def delete_pet(
    client_id: UUID,
    pet_id: UUID,
    current_clinic: CurrentClinic,
    db: DBSession,
):
    """Delete a pet."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.clinic_id == current_clinic.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    pet_result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.client_id == client_id)
    )
    pet = pet_result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    await db.delete(pet)
    await db.commit()
