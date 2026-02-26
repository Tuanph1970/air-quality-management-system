"""Command to submit a new sensor reading."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class SubmitReadingCommand:
    """Immutable command carrying pollutant measurements from a sensor.

    The application service calculates the AQI, saves the reading,
    and publishes a ``SensorReadingCreated`` event.
    """

    sensor_id: UUID
    pm25: float = 0.0
    pm10: float = 0.0
    co: float = 0.0
    co2: float = 0.0
    no2: float = 0.0
    nox: float = 0.0
    so2: float = 0.0
    o3: float = 0.0
    temperature: float = 0.0
    humidity: float = 0.0
    timestamp: Optional[datetime] = None

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid."""
        if self.sensor_id is None:
            raise ValueError("sensor_id is required")

        pollutants = {
            "pm25": self.pm25, "pm10": self.pm10,
            "co": self.co, "co2": self.co2,
            "no2": self.no2, "nox": self.nox,
            "so2": self.so2, "o3": self.o3,
        }
        for name, value in pollutants.items():
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value}")

        if self.humidity < 0.0 or self.humidity > 100.0:
            raise ValueError(
                f"Humidity must be between 0 and 100, got {self.humidity}"
            )
