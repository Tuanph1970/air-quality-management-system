"""Shared events module - Domain events for the AQMS system."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from .base_event import DomainEvent
from .factory_events import (  # noqa: F401
    FactoryCreated,
    FactoryUpdated,
    FactoryStatusChanged,
    FactorySuspended,
    FactoryResumed,
)
from .sensor_events import (  # noqa: F401
    SensorRegistered,
    SensorReadingCreated,
    SensorCalibrated,
    SensorStatusChanged,
)
from .alert_events import (  # noqa: F401
    ViolationDetected,
    ViolationResolved,
    AlertConfigUpdated,
)
from .user_events import (  # noqa: F401
    UserRegistered,
    UserPasswordChanged,
    UserLoggedIn,
)
from .fusion_events import (  # noqa: F401
    DataFusionCompleted,
    CalibrationUpdated,
    CrossValidationAlert,
)
from .satellite_events import (  # noqa: F401
    SatelliteDataFetched,
    SatelliteFetchFailed,
    ExcelDataImported,
    ExcelImportFailed,
)


# =============================================================================
# Station Service Events
# =============================================================================

@dataclass
class StationCreated(DomainEvent):
    """Event emitted when an air quality station is created."""
    station_id: UUID = None
    station_code: str = ""
    name: str = ""
    station_type: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    event_type: str = "station.created"


@dataclass
class StationActivated(DomainEvent):
    """Event emitted when a station is activated."""
    station_id: UUID = None
    event_type: str = "station.activated"


@dataclass
class StationDeactivated(DomainEvent):
    """Event emitted when a station is deactivated."""
    station_id: UUID = None
    reason: str = ""
    event_type: str = "station.deactivated"


@dataclass
class StationDataReceived(DomainEvent):
    """Event emitted when data is received from a station."""
    station_id: UUID = None
    timestamp: Optional[datetime] = None
    source: str = "STATION_API"
    event_type: str = "station.data.received"


@dataclass
class StationReadingsCreated(DomainEvent):
    """Event emitted when new readings are recorded."""
    station_id: UUID = None
    readings: Dict = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    source: str = "STATION_API"
    event_type: str = "station.readings.created"


# =============================================================================
# PurpleAir Events
# =============================================================================

@dataclass
class PurpleAirDataIngested(DomainEvent):
    """Event emitted when PurpleAir data is ingested."""
    sensor_id: UUID = None
    purpleair_sensor_id: int = 0
    readings: Dict = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    latitude: float = 0.0
    longitude: float = 0.0
    event_type: str = "purpleair.data.ingested"


@dataclass
class PurpleAirSensorRegistered(DomainEvent):
    """Event emitted when a PurpleAir sensor is registered."""
    sensor_id: UUID = None
    purpleair_sensor_id: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    event_type: str = "purpleair.sensor.registered"


# =============================================================================
# Alert Service - Additional Events
# =============================================================================

@dataclass
class AlertTriggered(DomainEvent):
    """Event emitted when an alert is triggered."""
    alert_id: UUID = None
    factory_id: UUID = None
    alert_type: str = ""
    severity: str = ""
    event_type: str = "alert.triggered"


# =============================================================================
# Air Quality Service Events
# =============================================================================

@dataclass
class AQICalculated(DomainEvent):
    """Event emitted when AQI is calculated."""
    location_id: UUID = None
    aqi: int = 0
    level: str = ""
    pollutants: Dict = field(default_factory=dict)
    event_type: str = "aqi.calculated"


@dataclass
class AQIForecastGenerated(DomainEvent):
    """Event emitted when AQI forecast is generated."""
    location_id: UUID = None
    forecast_date: str = ""
    aqi_min: int = 0
    aqi_max: int = 0
    event_type: str = "aqi.forecast.generated"


__all__ = [
    "DomainEvent",
    # Factory
    "FactoryCreated", "FactoryUpdated", "FactoryStatusChanged",
    "FactorySuspended", "FactoryResumed",
    # Sensor
    "SensorRegistered", "SensorReadingCreated", "SensorCalibrated",
    "SensorStatusChanged",
    # Alert
    "ViolationDetected", "ViolationResolved", "AlertConfigUpdated",
    "AlertTriggered",
    # User
    "UserRegistered", "UserPasswordChanged", "UserLoggedIn",
    # Fusion
    "DataFusionCompleted", "CalibrationUpdated", "CrossValidationAlert",
    # Satellite
    "SatelliteDataFetched", "SatelliteFetchFailed", "ExcelDataImported",
    "ExcelImportFailed",
    # Station
    "StationCreated", "StationActivated", "StationDeactivated",
    "StationDataReceived", "StationReadingsCreated",
    # PurpleAir
    "PurpleAirDataIngested", "PurpleAirSensorRegistered",
    # AQI
    "AQICalculated", "AQIForecastGenerated",
]
