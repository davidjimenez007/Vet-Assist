"""Main API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, appointments, conversations, analytics, settings, clinic, demo_requests, clients, chat
from app.api.v1 import client_auth, client_portal
from app.api.v1 import emergencies, follow_ups, webhooks

api_router = APIRouter()

# Staff/Veterinary endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(clinic.router, prefix="/clinic", tags=["clinic"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(demo_requests.router, prefix="/demo-requests", tags=["demo-requests"])

# WhatsApp automation endpoints
api_router.include_router(emergencies.router)
api_router.include_router(follow_ups.router)
api_router.include_router(webhooks.router)

# Client portal endpoints
api_router.include_router(client_auth.router, prefix="/client-auth", tags=["client-auth"])
api_router.include_router(client_portal.router, prefix="/portal", tags=["client-portal"])
