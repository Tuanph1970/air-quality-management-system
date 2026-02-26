"""Command to submit a sensor reading."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class SubmitReadingCommand:
    sensor_id: UUID
    pm25: float = 0.0
    pm10: float = 0.0
    co: float = 0.0
    no2: float = 0.0
    so2: float = 0.0
    o3: float = 0.0
