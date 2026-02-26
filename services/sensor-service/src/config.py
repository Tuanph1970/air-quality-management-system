"""Sensor service configuration via Pydantic Settings.

Reads configuration from environment variables with sensible defaults
for local development.  In Docker, values are injected via
``docker-compose.yml`` / ``.env``.

Usage::

    from src.config import settings

    engine = create_async_engine(settings.DATABASE_URL)
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — populated from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Service identity
    # ------------------------------------------------------------------
    SERVICE_NAME: str = "sensor-service"
    SERVICE_PORT: int = 8002

    # ------------------------------------------------------------------
    # Database (TimescaleDB — PostgreSQL extension)
    # ------------------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://aqms_user:aqms_pass@localhost:5433/sensor_db"
    )
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # ------------------------------------------------------------------
    # RabbitMQ
    # ------------------------------------------------------------------
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # ------------------------------------------------------------------
    # Auth / JWT
    # ------------------------------------------------------------------
    JWT_SECRET: str = "change-me-in-production-use-a-long-random-string"

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: str = "*"

    # ------------------------------------------------------------------
    # App meta
    # ------------------------------------------------------------------
    DEBUG: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()


# Module-level convenience alias.
settings = get_settings()
