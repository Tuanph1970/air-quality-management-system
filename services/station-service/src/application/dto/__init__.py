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


@dataclass
class RawDataDTO:
    """DTO for a single raw station data record."""

    id: UUID
    station_id: UUID
    measured_at: datetime
    # Pollutants
    no_value: Optional[float] = None
    o3_value: Optional[float] = None
    co_value: Optional[float] = None
    no2_value: Optional[float] = None
    nox_value: Optional[float] = None
    so2_value: Optional[float] = None
    pm10_value: Optional[float] = None
    pm25_value: Optional[float] = None
    # Environmental
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    # Wind
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    # Additional
    aqi: Optional[float] = None
    aqi_category: Optional[str] = None
    # Metadata
    source: str = "ENVISOFT_API"
    fetched_at: Optional[datetime] = None

    @classmethod
    def from_model(cls, model) -> "RawDataDTO":
        """Create DTO from RawStationDataModel."""
        return cls(
            id=UUID(model.id),
            station_id=UUID(model.station_id),
            measured_at=model.measured_at,
            no_value=model.no_value,
            o3_value=model.o3_value,
            co_value=model.co_value,
            no2_value=model.no2_value,
            nox_value=model.nox_value,
            so2_value=model.so2_value,
            pm10_value=model.pm10_value,
            pm25_value=model.pm25_value,
            temperature=model.temperature,
            humidity=model.humidity,
            pressure=model.pressure,
            wind_speed=model.wind_speed,
            wind_direction=model.wind_direction,
            aqi=model.aqi,
            aqi_category=model.aqi_category,
            source=model.source,
            fetched_at=model.fetched_at,
        )


@dataclass
class RawDataListDTO:
    """DTO for paginated list of raw data records."""

    items: List[RawDataDTO]
    total: int
    skip: int
    limit: int


@dataclass
class FetchRawDataResultDTO:
    """DTO for the result of a raw data fetch operation."""

    station_id: UUID
    records_fetched: int
    records_saved: int
    from_date: str
    to_date: str
    success: bool
    message: str
    error: Optional[str] = None
