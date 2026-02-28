"""Remote Sensing service configuration via Pydantic Settings.

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
    SERVICE_NAME: str = "remote-sensing-service"
    SERVICE_PORT: int = 8006

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = (
        "mysql+aiomysql://root:Mysql_2026@localhost:3306/remote_sensing_db?charset=utf8mb4"
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

    # ------------------------------------------------------------------
    # Satellite API keys (override via env)
    # ------------------------------------------------------------------
    NASA_EARTHDATA_TOKEN: str = ""
    COPERNICUS_API_KEY: str = ""
    SENTINEL_HUB_CLIENT_ID: str = ""
    SENTINEL_HUB_CLIENT_SECRET: str = ""

    # ------------------------------------------------------------------
    # Sensor Service (inter-service communication)
    # ------------------------------------------------------------------
    SENSOR_SERVICE_URL: str = "http://sensor-service:8002"

    # ------------------------------------------------------------------
    # Scheduler — CAMS fetch
    # ------------------------------------------------------------------
    CAMS_FETCH_ENABLED: bool = True
    CAMS_FETCH_CRON: str = "0 */6 * * *"  # Every 6 hours

    # ------------------------------------------------------------------
    # Scheduler — MODIS fetch
    # ------------------------------------------------------------------
    MODIS_FETCH_ENABLED: bool = True
    MODIS_FETCH_CRON: str = "0 2 * * *"  # Daily at 02:00 UTC

    # ------------------------------------------------------------------
    # Scheduler — TROPOMI fetch
    # ------------------------------------------------------------------
    TROPOMI_FETCH_ENABLED: bool = True
    TROPOMI_FETCH_CRON: str = "0 3 * * *"  # Daily at 03:00 UTC

    # ------------------------------------------------------------------
    # City bounding box (Ho Chi Minh City defaults)
    # ------------------------------------------------------------------
    CITY_BBOX_NORTH: float = 11.2
    CITY_BBOX_SOUTH: float = 10.3
    CITY_BBOX_EAST: float = 107.1
    CITY_BBOX_WEST: float = 106.3


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()


# Module-level convenience alias.
settings = get_settings()
