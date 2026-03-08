"""WRF simulation domain service."""
from typing import Optional

from ..value_objects.wrf_config import WRFConfig
from ..value_objects.bounding_box import BoundingBox


class WRFSimulationService:
    """Domain service for WRF simulation business logic."""

    @staticmethod
    def validate_simulation_config(config: WRFConfig) -> tuple[bool, Optional[str]]:
        """
        Validate WRF simulation configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check bounding box size
        if config.bounding_box.height_km > 5000:
            return False, "Domain height exceeds maximum of 5000 km"
        if config.bounding_box.width_km > 5000:
            return False, "Domain width exceeds maximum of 5000 km"

        # Check resolution vs domain size
        min_points = 10
        lat_points = config.bounding_box.height_km / config.horizontal_resolution_km
        lon_points = config.bounding_box.width_km / config.horizontal_resolution_km

        if lat_points < min_points or lon_points < min_points:
            return (
                False,
                f"Domain too small for {config.horizontal_resolution_km}km resolution. "
                f"Need at least {min_points}x{min_points} grid points.",
            )

        # Check memory estimate
        if config.estimated_memory_gb > 64:
            return (
                False,
                f"Estimated memory ({config.estimated_memory_gb}GB) exceeds available resources",
            )

        # Check simulation duration
        if config.simulation_hours > 168:  # 7 days
            return False, "Maximum simulation duration is 7 days (168 hours)"

        return True, None

    @staticmethod
    def estimate_runtime_hours(config: WRFConfig) -> float:
        """
        Estimate WRF runtime based on configuration.

        This is a rough estimate based on typical WRF performance:
        - ~1 minute per simulated hour per 100k grid points at 10km resolution
        - Scales with resolution and complexity
        """
        grid_points = config.estimated_grid_points
        base_minutes_per_hour = grid_points / 100000

        # Adjust for resolution (finer = slower)
        resolution_factor = 10 / config.horizontal_resolution_km

        # Adjust for vertical levels
        level_factor = config.vertical_levels / 30

        total_minutes = (
            base_minutes_per_hour
            * config.simulation_hours
            * resolution_factor
            * level_factor
        )

        return total_minutes / 60

    @staticmethod
    def recommend_configuration(
        center_lat: float,
        center_lon: float,
        region_radius_km: float,
        available_memory_gb: float = 16,
        max_runtime_hours: float = 4,
    ) -> WRFConfig:
        """
        Recommend WRF configuration based on region and constraints.

        Args:
            center_lat: Center latitude of region
            center_lon: Center longitude of region
            region_radius_km: Radius of region to simulate
            available_memory_gb: Available system memory
            max_runtime_hours: Maximum acceptable runtime

        Returns:
            Recommended WRFConfig
        """
        bounding_box = BoundingBox.from_center_and_radius(
            center_lat, center_lon, region_radius_km
        )

        # Start with coarse resolution and refine
        resolution = 27  # Start coarse
        vertical_levels = 30

        while resolution >= 3:
            config = WRFConfig(
                bounding_box=bounding_box,
                horizontal_resolution_km=resolution,
                vertical_levels=vertical_levels,
                simulation_hours=48,
            )

            if config.estimated_memory_gb <= available_memory_gb:
                estimated_runtime = WRFSimulationService.estimate_runtime_hours(config)
                if estimated_runtime <= max_runtime_hours:
                    return config

            resolution -= 3

        # If we can't find a good config, return the coarsest that fits in memory
        return WRFConfig(
            bounding_box=bounding_box,
            horizontal_resolution_km=27,
            vertical_levels=20,
            simulation_hours=24,
        )
