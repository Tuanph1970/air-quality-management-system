"""Configuration settings."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings."""
    
    SERVICE_NAME: str = "purpleair-ingestion-service"
    SERVICE_PORT: int = 8008
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    
    # PurpleAir
    PURPLEAIR_API_KEY: str = ""
    PURPLEAIR_USE_FAKE_DATA: bool = False
    PURPLEAIR_FAKE_DATA_INTERVAL: int = 60
    
    # Sensor mapping
    SENSOR_SERVICE_URL: str = "http://sensor-service:8002"
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment."""
        return cls(
            SERVICE_NAME=os.getenv("SERVICE_NAME", "purpleair-ingestion-service"),
            SERVICE_PORT=int(os.getenv("SERVICE_PORT", "8008")),
            DEBUG=os.getenv("DEBUG", "False").lower() in ("true", "1", "yes"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            RABBITMQ_URL=os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
            PURPLEAIR_API_KEY=os.getenv("PURPLEAIR_API_KEY", ""),
            PURPLEAIR_USE_FAKE_DATA=os.getenv("PURPLEAIR_USE_FAKE_DATA", "False").lower() in ("true", "1", "yes"),
            PURPLEAIR_FAKE_DATA_INTERVAL=int(os.getenv("PURPLEAIR_FAKE_DATA_INTERVAL", "60")),
            SENSOR_SERVICE_URL=os.getenv("SENSOR_SERVICE_URL", "http://sensor-service:8002"),
        )


settings = Settings.from_env()
