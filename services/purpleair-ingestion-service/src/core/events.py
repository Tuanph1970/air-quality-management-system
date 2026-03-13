"""PurpleAir event definitions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class PurpleAirDataIngested:
    """Event emitted when PurpleAir data is ingested."""

    event_id: Optional[UUID] = None
    sensor_id: Optional[UUID] = None
    purpleair_sensor_id: int = 0
    readings: dict = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    latitude: float = 0.0
    longitude: float = 0.0
    event_type: str = "purpleair.data.ingested"
    occurred_at: Optional[datetime] = field(default=None)

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
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else datetime.utcnow().isoformat(),
        }


@dataclass
class PurpleAirSensorRegistered:
    """Event emitted when PurpleAir sensor is registered."""

    event_id: Optional[UUID] = None
    sensor_id: Optional[UUID] = None
    purpleair_sensor_id: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    event_type: str = "purpleair.sensor.registered"
    occurred_at: Optional[datetime] = field(default=None)

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
            "latitude": self.latitude,
            "longitude": self.longitude,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else datetime.utcnow().isoformat(),
        }
