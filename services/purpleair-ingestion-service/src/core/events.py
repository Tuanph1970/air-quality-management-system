"""PurpleAir event definitions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class PurpleAirDataIngested:
    """Event emitted when PurpleAir data is ingested."""
    
    event_id: UUID
    sensor_id: UUID
    purpleair_sensor_id: int
    readings: dict
    timestamp: datetime
    latitude: float
    longitude: float
    event_type: str = "purpleair.data.ingested"
    
    def __post_init__(self):
        if self.event_id is None:
            self.event_id = uuid4()
        if self.occurred_at is None:
            self.occurred_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "event_id": str(self.event_id),
            "sensor_id": str(self.sensor_id),
            "purpleair_sensor_id": self.purpleair_sensor_id,
            "readings": self.readings,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "event_type": self.event_type,
            "occurred_at": datetime.utcnow().isoformat(),
        }


@dataclass
class PurpleAirSensorRegistered:
    """Event emitted when PurpleAir sensor is registered."""
    
    event_id: UUID
    sensor_id: UUID
    purpleair_sensor_id: int
    latitude: float
    longitude: float
    event_type: str = "purpleair.sensor.registered"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "event_id": str(self.event_id),
            "sensor_id": str(self.sensor_id),
            "purpleair_sensor_id": self.purpleair_sensor_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "event_type": self.event_type,
            "occurred_at": datetime.utcnow().isoformat(),
        }
