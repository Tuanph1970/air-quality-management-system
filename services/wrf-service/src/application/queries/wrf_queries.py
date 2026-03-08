"""Query definitions for WRF Service."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ...domain.entities.wrf_simulation import SimulationStatus


@dataclass
class GetWRFSimulationQuery:
    """Query to get a single WRF simulation by ID."""

    simulation_id: UUID


@dataclass
class ListWRFSimulationsQuery:
    """Query to list WRF simulations with optional filtering."""

    status: Optional[SimulationStatus] = None
    skip: int = 0
    limit: int = 20


@dataclass
class GetWRFForecastDataQuery:
    """Query to get forecast data for a specific variable."""

    simulation_id: UUID
    variable: str  # temperature, humidity, wind_speed, etc.
    level: str = "surface"  # surface, 10m, 2m, etc.
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class GetWRFSimulationStatusQuery:
    """Query to get current status of a simulation."""

    simulation_id: UUID


@dataclass
class GetRecommendedConfigQuery:
    """Query to get recommended WRF configuration for a region."""

    center_lat: float
    center_lon: float
    region_radius_km: float
    available_memory_gb: float = 16.0
    max_runtime_hours: float = 4.0
