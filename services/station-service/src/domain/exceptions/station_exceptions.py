"""Station domain exceptions."""
from __future__ import annotations

from typing import Any, Optional


class StationDomainError(Exception):
    """Base exception for all station domain errors."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class StationNotFoundError(StationDomainError):
    """Raised when a station is not found."""
    
    def __init__(self, station_id: str | Any, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=f"Station not found: {station_id}",
            details={"station_id": str(station_id), **(details or {})},
        )


class StationAlreadyExistsError(StationDomainError):
    """Raised when trying to create a station that already exists."""
    
    def __init__(
        self,
        identifier: str,
        identifier_type: str = "station_code",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"Station already exists with {identifier_type}: {identifier}",
            details={
                "identifier": identifier,
                "identifier_type": identifier_type,
                **(details or {}),
            },
        )


class InvalidStationConfigurationError(StationDomainError):
    """Raised when station configuration is invalid."""
    
    def __init__(self, reason: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=f"Invalid station configuration: {reason}",
            details={"reason": reason, **(details or {})},
        )


class StationAPIConfigurationError(StationDomainError):
    """Raised when station API configuration is invalid."""
    
    def __init__(
        self,
        reason: str,
        endpoint: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"Station API configuration error: {reason}",
            details={
                "reason": reason,
                "endpoint": endpoint,
                **(details or {}),
            },
        )


class InvalidPollutantReadingError(StationDomainError):
    """Raised when pollutant reading values are invalid."""
    
    def __init__(
        self,
        pollutant: str,
        value: float,
        reason: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"Invalid reading for {pollutant}: {value} - {reason}",
            details={
                "pollutant": pollutant,
                "value": value,
                "reason": reason,
                **(details or {}),
            },
        )


class StationDataValidationError(StationDomainError):
    """Raised when station data validation fails."""
    
    def __init__(self, reason: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=f"Station data validation failed: {reason}",
            details={"reason": reason, **(details or {})},
        )


class StationOfflineError(StationDomainError):
    """Raised when trying to perform operations on an offline station."""
    
    def __init__(self, station_id: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=f"Station is offline: {station_id}",
            details={"station_id": station_id, **(details or {})},
        )


class StationAlreadyActiveError(StationDomainError):
    """Raised when trying to activate an already active station."""
    
    def __init__(self, station_id: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=f"Station is already active: {station_id}",
            details={"station_id": station_id, **(details or {})},
        )
