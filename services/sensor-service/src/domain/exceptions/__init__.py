"""Sensor service domain exceptions."""
from .sensor_exceptions import (
    CalibrationError,
    InvalidReadingError,
    InvalidSensorStatusError,
    SensorAlreadyExistsError,
    SensorAlreadyOnlineError,
    SensorDomainError,
    SensorNotCalibratedError,
    SensorNotFoundError,
    SensorOfflineError,
)

__all__ = [
    "CalibrationError",
    "InvalidReadingError",
    "InvalidSensorStatusError",
    "SensorAlreadyExistsError",
    "SensorAlreadyOnlineError",
    "SensorDomainError",
    "SensorNotCalibratedError",
    "SensorNotFoundError",
    "SensorOfflineError",
]
