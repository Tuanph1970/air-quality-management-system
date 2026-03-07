"""Data Transfer Objects (DTOs) for the station service."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class StationDTO:
    """DTO for station data."""
    
    id: UUID
    station_code: str
    name: str
    station_type: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    is_active: bool = False
    is_configured: bool = False
    api_endpoint: Optional[str] = None
    poll_interval_seconds: Optional[int] = None
    data_retention_days: int = 1
    last_data_received: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_entity(cls, station) -> "StationDTO":
        """Create DTO from Station entity."""
        return cls(
            id=station.id,
            station_code=station.station_code,
            name=station.name,
            station_type=station.station_type.value,
            latitude=station.location.latitude,
            longitude=station.location.longitude,
            altitude=station.location.altitude,
            is_active=station.is_active,
            is_configured=station.is_configured,
            api_endpoint=station.api_config.get("endpoint") if station.api_config else None,
            poll_interval_seconds=station.api_config.get("poll_interval_seconds") if station.api_config else None,
            data_retention_days=station.data_retention_days,
            last_data_received=station.last_data_received,
            metadata=station.metadata,
            created_at=station.created_at,
            updated_at=station.updated_at,
        )


@dataclass
class StationListDTO:
    """DTO for paginated list of stations."""
    
    items: List[StationDTO]
    total: int
    skip: int
    limit: int


@dataclass
class PollutantReadingDTO:
    """DTO for a single pollutant reading."""
    
    id: UUID
    station_id: UUID
    pollutant_type: str
    value: float
    unit: str
    quality_flag: Optional[str]
    timestamp: datetime
    created_at: datetime
    
    @classmethod
    def from_entity(cls, reading) -> "PollutantReadingDTO":
        """Create DTO from PollutantReading entity."""
        return cls(
            id=reading.id,
            station_id=reading.station_id,
            pollutant_type=reading.pollutant_type.value,
            value=reading.value,
            unit=reading.unit,
            quality_flag=reading.quality_flag,
            timestamp=reading.timestamp,
            created_at=reading.created_at,
        )


@dataclass
class StationReadingsDTO:
    """DTO for station readings with multiple pollutants."""
    
    station_id: UUID
    station_name: str
    timestamp: datetime
    readings: Dict[str, float]
    source: str
    
    @classmethod
    def from_batch(cls, batch, station_name: str = "") -> "StationReadingsDTO":
        """Create DTO from StationReadingBatch."""
        return cls(
            station_id=batch.station_id,
            station_name=station_name,
            timestamp=batch.timestamp,
            readings=batch.get_all_values(),
            source=batch.source,
        )


@dataclass
class StationReadingsListDTO:
    """DTO for paginated list of readings."""
    
    items: List[PollutantReadingDTO]
    total: int
    skip: int
    limit: int
