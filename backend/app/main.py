"""FastAPI application entry point."""

print("=" * 50)
print("VETASSIST STARTING - Deploy version 2026-02-03 v4")
print("=" * 50)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("[STARTUP] Importing settings...")
from app.config import settings
print(f"[STARTUP] Settings loaded, environment: {settings.environment}")

print("[STARTUP] Importing database...")
from app.database import init_db, close_db
print("[STARTUP] Database module imported")

from app.api.v1.router import api_router
from app.api.webhooks import webhooks_router
print("[STARTUP] All imports complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("[LIFESPAN] Starting database initialization...")
    try:
        await init_db()
        print("[LIFESPAN] Database initialized successfully!")
    except Exception as e:
        print(f"[LIFESPAN] Database init FAILED: {e}")
        raise
    yield
    # Shutdown
    print("[LIFESPAN] Shutting down, closing database...")
    await close_db()
    print("[LIFESPAN] Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Receptionist and Smart Scheduling for Veterinary Clinics",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(webhooks_router, prefix="/webhooks")

print("[STARTUP] FastAPI app configured, ready to start!")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }

