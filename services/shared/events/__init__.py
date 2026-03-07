"""Shared events module - Domain events for the AQMS system."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base class for all domain events.
    
    Attributes:
        event_id: Unique event identifier
        occurred_at: When the event occurred
        event_type: Type identifier for the event
    """
    
    event_id: UUID
    occurred_at: datetime
    event_type: str
    
    def __post_init__(self):
        if self.event_id is None:
            self.event_id = uuid4()
        if self.occurred_at is None:
            self.occurred_at = datetime.utcnow()


# =============================================================================
# Factory Service Events
# =============================================================================

@dataclass
class FactoryCreated(DomainEvent):
    """Event emitted when a factory is created."""
    factory_id: UUID
    name: str
    event_type: str = "factory.created"


@dataclass
class FactoryStatusChanged(DomainEvent):
    """Event emitted when factory status changes."""
    factory_id: UUID
    old_status: str
    new_status: str
    reason: str = ""
    event_type: str = "factory.status.changed"


@dataclass
class FactorySuspended(DomainEvent):
    """Event emitted when a factory is suspended."""
    factory_id: UUID
    reason: str
    suspended_by: UUID
    event_type: str = "factory.suspended"


# =============================================================================
# Sensor Service Events
# =============================================================================

@dataclass
class SensorReadingCreated(DomainEvent):
    """Event emitted when a sensor reading is created."""
    sensor_id: UUID
    factory_id: UUID
    pm25: float
    pm10: float
    aqi: int
    timestamp: datetime
    event_type: str = "sensor.reading.created"


@dataclass
class SensorRegistered(DomainEvent):
    """Event emitted when a sensor is registered."""
    sensor_id: UUID
    factory_id: UUID
    sensor_type: str
    latitude: float
    longitude: float
    event_type: str = "sensor.registered"


@dataclass
class SensorCalibrated(DomainEvent):
    """Event emitted when a sensor is calibrated."""
    sensor_id: UUID
    calibrated_by: UUID
    offset: float
    scale_factor: float
    event_type: str = "sensor.calibrated"


# =============================================================================
# Station Service Events (NEW)
# =============================================================================

@dataclass
class StationCreated(DomainEvent):
    """Event emitted when an air quality station is created."""
    station_id: UUID
    station_code: str
    name: str
    station_type: str
    latitude: float
    longitude: float
    event_type: str = "station.created"


@dataclass
class StationActivated(DomainEvent):
    """Event emitted when a station is activated."""
    station_id: UUID
    event_type: str = "station.activated"


@dataclass
class StationDeactivated(DomainEvent):
    """Event emitted when a station is deactivated."""
    station_id: UUID
    reason: str = ""
    event_type: str = "station.deactivated"


@dataclass
class StationDataReceived(DomainEvent):
    """Event emitted when data is received from a station.
    
    This event triggers AQI recalculation in the air-quality-service.
    """
    station_id: UUID
    timestamp: datetime
    source: str = "STATION_API"
    event_type: str = "station.data.received"


@dataclass
class StationReadingsCreated(DomainEvent):
    """Event emitted when new readings are recorded."""
    station_id: UUID
    readings: dict  # pollutant_name -> value
    timestamp: datetime
    source: str = "STATION_API"
    event_type: str = "station.readings.created"


# =============================================================================
# PurpleAir Events (NEW)
# =============================================================================

@dataclass
class PurpleAirDataIngested(DomainEvent):
    """Event emitted when PurpleAir data is ingested.
    
    This event triggers AQI recalculation in the air-quality-service.
    """
    sensor_id: UUID
    purpleair_sensor_id: int
    readings: dict  # pollutant_name -> value
    timestamp: datetime
    latitude: float
    longitude: float
    event_type: str = "purpleair.data.ingested"


@dataclass
class PurpleAirSensorRegistered(DomainEvent):
    """Event emitted when a PurpleAir sensor is registered."""
    sensor_id: UUID
    purpleair_sensor_id: int
    latitude: float
    longitude: float
    event_type: str = "purpleair.sensor.registered"


# =============================================================================
# Alert Service Events
# =============================================================================

@dataclass
class ViolationDetected(DomainEvent):
    """Event emitted when a violation is detected."""
    violation_id: UUID
    factory_id: UUID
    pollutant: str
    measured_value: float
    threshold: float
    severity: str
    event_type: str = "alert.violation.detected"


@dataclass
class ViolationResolved(DomainEvent):
    """Event emitted when a violation is resolved."""
    violation_id: UUID
    factory_id: UUID
    resolved_by: UUID
    event_type: str = "alert.violation.resolved"


@dataclass
class AlertTriggered(DomainEvent):
    """Event emitted when an alert is triggered."""
    alert_id: UUID
    factory_id: UUID
    alert_type: str
    severity: str
    event_type: str = "alert.triggered"


# =============================================================================
# Air Quality Service Events
# =============================================================================

@dataclass
class AQICalculated(DomainEvent):
    """Event emitted when AQI is calculated."""
    location_id: UUID
    aqi: int
    level: str
    pollutants: dict
    event_type: str = "aqi.calculated"


@dataclass
class AQIForecastGenerated(DomainEvent):
    """Event emitted when AQI forecast is generated."""
    location_id: UUID
    forecast_date: str
    aqi_min: int
    aqi_max: int
    event_type: str = "aqi.forecast.generated"
