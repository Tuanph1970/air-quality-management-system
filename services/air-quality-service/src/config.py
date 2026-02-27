"""Air Quality Service configuration via Pydantic Settings.

Reads configuration from environment variables with sensible defaults
for local development.  In Docker, values are injected via
``docker-compose.yml`` / ``.env``.

Usage::

    from src.config import settings

    redis_client = redis.from_url(settings.REDIS_URL)
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
    SERVICE_NAME: str = "air-quality-service"
    SERVICE_PORT: int = 8004

    # ------------------------------------------------------------------
    # Redis (for caching AQI calculations)
    # ------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PREFIX: str = "aqms:aqi"
    CACHE_TTL_DEFAULT: int = 300  # 5 minutes
    CACHE_TTL_MAP_DATA: int = 600  # 10 minutes
    CACHE_TTL_FORECAST: int = 1800  # 30 minutes

    # ------------------------------------------------------------------
    # RabbitMQ
    # ------------------------------------------------------------------
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # ------------------------------------------------------------------
    # External APIs
    # ------------------------------------------------------------------
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_AIR_QUALITY_ENDPOINT: str = "https://airquality.googleapis.com/v1/currentConditions"

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
