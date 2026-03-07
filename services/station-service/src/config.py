"""Configuration settings for station service."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""
    
    # Service identity
    SERVICE_NAME: str = "station-service"
    SERVICE_PORT: int = 8007
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "mysql+aiomysql://root:password@localhost:3306/station_db"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # External services
    SENSOR_SERVICE_URL: str = "http://sensor-service:8002"
    AIR_QUALITY_SERVICE_URL: str = "http://air-quality-service:8004"
    
    # Data collection
    DEFAULT_POLL_INTERVAL: int = 300  # 5 minutes
    DATA_RETENTION_DAYS: int = 1
    USE_FAKE_DATA: bool = False
    
    # Fake data generation
    FAKE_DATA_STATION_COUNT: int = 5
    FAKE_DATA_INTERVAL_SECONDS: int = 60
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables.
        
        Returns:
            Settings instance
        """
        return cls(
            SERVICE_NAME=os.getenv("SERVICE_NAME", "station-service"),
            SERVICE_PORT=int(os.getenv("SERVICE_PORT", "8007")),
            DEBUG=os.getenv("DEBUG", "False").lower() in ("true", "1", "yes"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            DATABASE_URL=os.getenv(
                "DATABASE_URL",
                "mysql+aiomysql://root:Mysql_2026@mysql:3306/station_db?charset=utf8mb4",
            ),
            RABBITMQ_URL=os.getenv(
                "RABBITMQ_URL",
                "amqp://guest:guest@rabbitmq:5672/",
            ),
            SENSOR_SERVICE_URL=os.getenv("SENSOR_SERVICE_URL", "http://sensor-service:8002"),
            AIR_QUALITY_SERVICE_URL=os.getenv("AIR_QUALITY_SERVICE_URL", "http://air-quality-service:8004"),
            DEFAULT_POLL_INTERVAL=int(os.getenv("DEFAULT_POLL_INTERVAL", "300")),
            DATA_RETENTION_DAYS=int(os.getenv("DATA_RETENTION_DAYS", "1")),
            USE_FAKE_DATA=os.getenv("USE_FAKE_DATA", "False").lower() in ("true", "1", "yes"),
            FAKE_DATA_STATION_COUNT=int(os.getenv("FAKE_DATA_STATION_COUNT", "5")),
            FAKE_DATA_INTERVAL_SECONDS=int(os.getenv("FAKE_DATA_INTERVAL_SECONDS", "60")),
        )


# Global settings instance
settings = Settings.from_env()
