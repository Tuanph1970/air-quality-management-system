"""Command to calibrate a sensor."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class CalibrateSensorCommand:
    sensor_id: UUID
    offset: float
    scale_factor: float
    calibrated_by: UUID
