"""Command to register a new sensor."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class RegisterSensorCommand:
    factory_id: UUID
    sensor_type: str
    latitude: float
    longitude: float
