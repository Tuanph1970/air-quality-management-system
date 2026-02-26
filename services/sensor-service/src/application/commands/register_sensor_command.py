"""Command to register a new sensor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import UUID


@dataclass(frozen=True)
class RegisterSensorCommand:
    """Immutable command carrying all data needed to register a sensor.

    Validated by the application service before domain entity creation.
    """

    serial_number: str
    sensor_type: str
    model: str
    latitude: float
    longitude: float
    factory_id: Optional[UUID] = None
    calibration_params: Dict = field(default_factory=dict)

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid."""
        if not self.serial_number or not self.serial_number.strip():
            raise ValueError("Serial number is required")
        if not self.sensor_type or not self.sensor_type.strip():
            raise ValueError("Sensor type is required")
        if not self.model or not self.model.strip():
            raise ValueError("Sensor model is required")
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")
