"""Configuration settings."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass(frozen=True)
class PurpleAirSensorConfig:
    """Configuration for a single PurpleAir sensor."""
    sensor_id: int
    api_key: str
    name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    SERVICE_NAME: str = "purpleair-ingestion-service"
    SERVICE_PORT: int = 8008
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # PurpleAir Cloud API
    PURPLEAIR_API_KEY: str = ""
    PURPLEAIR_USE_FAKE_DATA: bool = False
    PURPLEAIR_FAKE_DATA_INTERVAL: int = 60
    
    # PurpleAir Cloud Polling
    PURPLEAIR_POLLING_INTERVAL_HOURS: int = 2
    PURPLEAIR_RAW_DATA_DIR: str = "./data/purpleair/raw"
    PURPLEAIR_SENSORS: List[PurpleAirSensorConfig] = field(default_factory=list)

    # Sensor mapping
    SENSOR_SERVICE_URL: str = "http://sensor-service:8002"

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment."""
        # Parse PurpleAir sensors from JSON environment variable
        sensors_json = os.getenv("PURPLEAIR_SENSORS", "[]")
        sensors = []
        try:
            sensors_data = json.loads(sensors_json)
            for s in sensors_data:
                sensors.append(PurpleAirSensorConfig(
                    sensor_id=int(s.get("sensor_id", 0)),
                    api_key=s.get("api_key", ""),
                    name=s.get("name", ""),
                    latitude=float(s.get("latitude", 0.0)),
                    longitude=float(s.get("longitude", 0.0)),
                ))
        except (json.JSONDecodeError, ValueError) as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to parse PURPLEAIR_SENSORS: {e}")

        return cls(
            SERVICE_NAME=os.getenv("SERVICE_NAME", "purpleair-ingestion-service"),
            SERVICE_PORT=int(os.getenv("SERVICE_PORT", "8008")),
            DEBUG=os.getenv("DEBUG", "False").lower() in ("true", "1", "yes"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            RABBITMQ_URL=os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
            PURPLEAIR_API_KEY=os.getenv("PURPLEAIR_API_KEY", ""),
            PURPLEAIR_USE_FAKE_DATA=os.getenv("PURPLEAIR_USE_FAKE_DATA", "False").lower() in ("true", "1", "yes"),
            PURPLEAIR_FAKE_DATA_INTERVAL=int(os.getenv("PURPLEAIR_FAKE_DATA_INTERVAL", "60")),
            PURPLEAIR_POLLING_INTERVAL_HOURS=int(os.getenv("PURPLEAIR_POLLING_INTERVAL_HOURS", "2")),
            PURPLEAIR_RAW_DATA_DIR=os.getenv("PURPLEAIR_RAW_DATA_DIR", "./data/purpleair/raw"),
            PURPLEAIR_SENSORS=sensors,
            SENSOR_SERVICE_URL=os.getenv("SENSOR_SERVICE_URL", "http://sensor-service:8002"),
        )


settings = Settings.from_env()
