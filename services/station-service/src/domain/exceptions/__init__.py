"""Domain exceptions for the station service."""
from __future__ import annotations

from .station_exceptions import (
    StationDomainError,
    StationNotFoundError,
    StationAlreadyExistsError,
    InvalidStationConfigurationError,
    StationAPIConfigurationError,
    InvalidPollutantReadingError,
    StationDataValidationError,
    StationOfflineError,
    StationAlreadyActiveError,
)

__all__ = [
    "StationDomainError",
    "StationNotFoundError",
    "StationAlreadyExistsError",
    "InvalidStationConfigurationError",
    "StationAPIConfigurationError",
    "InvalidPollutantReadingError",
    "StationDataValidationError",
    "StationOfflineError",
    "StationAlreadyActiveError",
]
