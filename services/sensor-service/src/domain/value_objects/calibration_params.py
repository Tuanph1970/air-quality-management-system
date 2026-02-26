"""Calibration parameters value object."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CalibrationParams:
    """Value Object for sensor calibration parameters."""

    offset: float = 0.0
    scale_factor: float = 1.0
    calibrated_at: datetime = None
    calibrated_by: str = ""
