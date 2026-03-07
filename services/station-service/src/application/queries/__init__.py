"""Application queries - Read operations (CQRS)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class GetStationQuery:
    """Query to get a single station by ID."""
    
    station_id: UUID


@dataclass
class GetStationByCodeQuery:
    """Query to get a station by external code."""
    
    station_code: str


@dataclass
class ListStationsQuery:
    """Query to list stations with filters."""
    
    station_type: Optional[str] = None
    is_active: Optional[bool] = None
    skip: int = 0
    limit: int = 20


@dataclass
class GetNearbyStationsQuery:
    """Query to find stations near a location."""
    
    latitude: float
    longitude: float
    radius_km: float = 10.0
    limit: int = 10


@dataclass
class GetStationReadingsQuery:
    """Query to get readings for a station."""
    
    station_id: UUID
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    pollutant_type: Optional[str] = None
    skip: int = 0
    limit: int = 100


@dataclass
class GetLatestStationReadingsQuery:
    """Query to get latest readings for a station."""
    
    station_id: UUID
    pollutant_types: Optional[list] = None
