"""Application configuration settings."""

import logging
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "VetAssist AI"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vetassist"
    database_echo: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url_scheme(cls, v: str) -> str:
        """Transform Railway's postgres:// to postgresql+asyncpg:// for SQLAlchemy async."""
        if v and v.startswith("postgres://"):
            transformed = v.replace("postgres://", "postgresql+asyncpg://", 1)
            # Log transformation (hide password)
            safe_url = transformed.split("@")[-1] if "@" in transformed else "localhost"
            logger.info(f"DATABASE_URL transformed: postgres:// -> postgresql+asyncpg:// (host: {safe_url})")
            return transformed
        return v

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_whatsapp_number: str = ""

    # AI (OpenAI-compatible: works with OpenAI, Gemini, Groq, etc.)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str = ""  # Leave empty for OpenAI, or set for Gemini/Groq

    # Email (SMTP)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "VetAssist"
    notification_email: str = ""  # Where to send demo request notifications

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Timezone
    default_timezone: str = "America/Bogota"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    s = Settings()
    # Log database URL info (hide credentials)
    if s.database_url:
        host_part = s.database_url.split("@")[-1] if "@" in s.database_url else "localhost"
        scheme = s.database_url.split("://")[0] if "://" in s.database_url else "unknown"
        logger.info(f"Settings loaded - DB scheme: {scheme}, host: {host_part}")
    return s


settings = get_settings()

