"""Command to calibrate a sensor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import UUID


@dataclass(frozen=True)
class CalibrateSensorCommand:
    """Immutable command carrying calibration parameters for a sensor.

    Validated by the application service before applying to the domain entity.
    """

    sensor_id: UUID
    calibration_params: Dict = field(default_factory=dict)
    calibrated_by: Optional[UUID] = None

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid."""
        if self.sensor_id is None:
            raise ValueError("sensor_id is required")
        if not self.calibration_params:
            raise ValueError("calibration_params must not be empty")
