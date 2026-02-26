"""Sensor domain exceptions.

Each exception maps to a specific business rule violation.  The interface
layer translates these into appropriate HTTP status codes.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations


class SensorDomainError(Exception):
    """Base exception for all sensor domain errors."""

    def __init__(self, detail: str = "Sensor domain error") -> None:
        self.detail = detail
        super().__init__(self.detail)


# ------------------------------------------------------------------
# Sensor entity errors
# ------------------------------------------------------------------
class SensorNotFoundError(SensorDomainError):
    """Raised when a sensor cannot be found by its ID or serial number."""

    def __init__(self, identifier: str = "") -> None:
        detail = (
            f"Sensor '{identifier}' not found"
            if identifier
            else "Sensor not found"
        )
        super().__init__(detail)


class SensorAlreadyExistsError(SensorDomainError):
    """Raised when trying to register a duplicate serial number."""

    def __init__(self, serial_number: str = "") -> None:
        detail = (
            f"Sensor with serial number '{serial_number}' already exists"
            if serial_number
            else "Sensor already exists"
        )
        super().__init__(detail)


class SensorOfflineError(SensorDomainError):
    """Raised when an operation requires the sensor to be online."""

    def __init__(self) -> None:
        super().__init__("Sensor is offline and cannot accept readings")


class SensorAlreadyOnlineError(SensorDomainError):
    """Raised when trying to bring an already-online sensor online."""

    def __init__(self) -> None:
        super().__init__("Sensor is already online")


class InvalidSensorStatusError(SensorDomainError):
    """Raised for invalid status transitions."""

    def __init__(self, current: str = "", target: str = "") -> None:
        detail = (
            f"Cannot transition from {current} to {target}"
            if current and target
            else "Invalid sensor status transition"
        )
        super().__init__(detail)


# ------------------------------------------------------------------
# Reading entity errors
# ------------------------------------------------------------------
class InvalidReadingError(SensorDomainError):
    """Raised when a sensor reading contains invalid data."""

    def __init__(self, detail: str = "Invalid sensor reading") -> None:
        super().__init__(detail)


# ------------------------------------------------------------------
# Calibration errors
# ------------------------------------------------------------------
class SensorNotCalibratedError(SensorDomainError):
    """Raised when an operation requires calibration data."""

    def __init__(self) -> None:
        super().__init__("Sensor has not been calibrated")


class CalibrationError(SensorDomainError):
    """Raised when calibration parameters are invalid."""

    def __init__(self, detail: str = "Invalid calibration parameters") -> None:
        super().__init__(detail)
