"""WRF Simulation Configuration value object."""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

from .bounding_box import BoundingBox


class MicrophysicsScheme(Enum):
    """Microphysics parameterization schemes."""

    WSM3 = "wsmd3"
    WSM5 = "wsmd5"
    WSM6 = "wsmd6"
    THOMPSON = "thompson"
    MORRISON = "morrison"


class LongwaveRadiationScheme(Enum):
    """Longwave radiation schemes."""

    RRTM = "rrtm"
    CAM = "cam"
    NEWCAM = "newcam"


class ShortwaveRadiationScheme(Enum):
    """Shortwave radiation schemes."""

    DUDHIA = "dudhia"
    CAM = "cam"
    RRTMG = "rrtmg"


class LandSurfaceModel(Enum):
    """Land surface models."""

    NOAH = "noah"
    RUC = "ruc"
    CLM4 = "clm4"


class PlanetaryBoundaryLayerScheme(Enum):
    """PBL schemes."""

    YSU = "ysu"
    MYNN = "mynn"
    BouLac = "bouLac"


@dataclass(frozen=True)
class PhysicsOptions:
    """Physics parameterization options for WRF."""

    microphysics: MicrophysicsScheme = MicrophysicsScheme.WSM6
    longwave_radiation: LongwaveRadiationScheme = LongwaveRadiationScheme.RRTM
    shortwave_radiation: ShortwaveRadiationScheme = ShortwaveRadiationScheme.DUDHIA
    land_surface: LandSurfaceModel = LandSurfaceModel.NOAH
    pbl_scheme: PlanetaryBoundaryLayerScheme = PlanetaryBoundaryLayerScheme.YSU

    def to_wrf_namelist(self) -> dict:
        """Convert to WRF namelist format."""
        return {
            "mp_physics": list(MicrophysicsScheme).index(self.microphysics) + 1,
            "ra_lw_physics": list(LongwaveRadiationScheme).index(self.longwave_radiation) + 1,
            "ra_sw_physics": list(ShortwaveRadiationScheme).index(self.shortwave_radiation) + 1,
            "sf_surface_physics": list(LandSurfaceModel).index(self.land_surface) + 1,
            "sf_pbl_physics": list(PlanetaryBoundaryLayerScheme).index(self.pbl_scheme) + 1,
        }


@dataclass
class WRFConfig:
    """Value Object - WRF simulation configuration."""

    bounding_box: BoundingBox
    horizontal_resolution_km: float
    vertical_levels: int
    simulation_hours: int
    physics_options: PhysicsOptions = field(default_factory=PhysicsOptions)
    nest_ratio: List[int] = field(default_factory=lambda: [3])
    output_interval_hours: int = 1
    start_date: Optional[str] = None

    def __post_init__(self):
        """Validate configuration."""
        if self.horizontal_resolution_km < 1:
            raise ValueError("Horizontal resolution must be at least 1 km")
        if self.vertical_levels < 10:
            raise ValueError("Must have at least 10 vertical levels")
        if self.simulation_hours < 1:
            raise ValueError("Simulation must be at least 1 hour")

    @property
    def estimated_grid_points(self) -> int:
        """Estimate number of grid points."""
        lat_points = int(self.bounding_box.height_km / self.horizontal_resolution_km)
        lon_points = int(self.bounding_box.width_km / self.horizontal_resolution_km)
        return lat_points * lon_points * self.vertical_levels

    @property
    def estimated_memory_gb(self) -> float:
        """Estimate memory requirement in GB."""
        grid_points = self.estimated_grid_points
        bytes_per_point = 8 * 50  # ~50 variables, 8 bytes each
        return (grid_points * bytes_per_point) / (1024 ** 3)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "bounding_box": self.bounding_box.to_dict(),
            "horizontal_resolution_km": self.horizontal_resolution_km,
            "vertical_levels": self.vertical_levels,
            "simulation_hours": self.simulation_hours,
            "physics_options": {
                "microphysics": self.physics_options.microphysics.value,
                "longwave_radiation": self.physics_options.longwave_radiation.value,
                "shortwave_radiation": self.physics_options.shortwave_radiation.value,
                "land_surface": self.physics_options.land_surface.value,
                "pbl_scheme": self.physics_options.pbl_scheme.value,
            },
            "nest_ratio": self.nest_ratio,
            "output_interval_hours": self.output_interval_hours,
            "start_date": self.start_date,
            "estimated_grid_points": self.estimated_grid_points,
            "estimated_memory_gb": round(self.estimated_memory_gb, 2),
        }
