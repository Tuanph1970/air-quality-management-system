"""Command to create a new WRF simulation."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ...domain.value_objects.wrf_config import (
    WRFConfig,
    PhysicsOptions,
    MicrophysicsScheme,
    LongwaveRadiationScheme,
    ShortwaveRadiationScheme,
    LandSurfaceModel,
    PlanetaryBoundaryLayerScheme,
)
from ...domain.value_objects.bounding_box import BoundingBox


@dataclass
class CreateWRFSimulationCommand:
    """Command to create a new WRF simulation."""

    name: str
    # Bounding box parameters
    north: float
    south: float
    east: float
    west: float
    # Simulation parameters
    horizontal_resolution_km: float
    vertical_levels: int
    simulation_hours: int
    output_interval_hours: int = 1
    # Optional start date (ISO format string)
    start_date: Optional[str] = None
    # Physics options (optional, will use defaults if not provided)
    microphysics: str = "wsmd6"
    longwave_radiation: str = "rrtm"
    shortwave_radiation: str = "dudhia"
    land_surface: str = "noah"
    pbl_scheme: str = "ysu"

    def to_config(self) -> WRFConfig:
        """Convert command to WRFConfig."""
        bounding_box = BoundingBox(
            north=self.north,
            south=self.south,
            east=self.east,
            west=self.west,
        )

        physics_options = PhysicsOptions(
            microphysics=MicrophysicsScheme(self.microphysics),
            longwave_radiation=LongwaveRadiationScheme(self.longwave_radiation),
            shortwave_radiation=ShortwaveRadiationScheme(self.shortwave_radiation),
            land_surface=LandSurfaceModel(self.land_surface),
            pbl_scheme=PlanetaryBoundaryLayerScheme(self.pbl_scheme),
        )

        return WRFConfig(
            bounding_box=bounding_box,
            horizontal_resolution_km=self.horizontal_resolution_km,
            vertical_levels=self.vertical_levels,
            simulation_hours=self.simulation_hours,
            physics_options=physics_options,
            output_interval_hours=self.output_interval_hours,
            start_date=self.start_date,
        )


@dataclass
class StartWRFSimulationCommand:
    """Command to start a WRF simulation."""

    simulation_id: UUID


@dataclass
class CancelWRFSimulationCommand:
    """Command to cancel a running WRF simulation."""

    simulation_id: UUID


@dataclass
class DeleteWRFSimulationCommand:
    """Command to delete a WRF simulation."""

    simulation_id: UUID
