"""Webhook routers for Twilio."""

from fastapi import APIRouter

from app.api.webhooks.voice import router as voice_router
from app.api.webhooks.whatsapp import router as whatsapp_router

webhooks_router = APIRouter(tags=["webhooks"])
webhooks_router.include_router(voice_router, prefix="/voice")
webhooks_router.include_router(whatsapp_router, prefix="/whatsapp")
