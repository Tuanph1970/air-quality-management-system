"""Query handlers for WRF Service."""
import logging
from typing import List, Optional
from uuid import UUID

from ...domain.entities.wrf_simulation import WRFSimulation, SimulationStatus
from ...domain.repositories.wrf_simulation_repository import WRFSimulationRepository
from ...domain.services.wrf_simulation_service import WRFSimulationService
from .wrf_queries import (
    GetWRFSimulationQuery,
    ListWRFSimulationsQuery,
    GetWRFForecastDataQuery,
    GetWRFSimulationStatusQuery,
    GetRecommendedConfigQuery,
)

logger = logging.getLogger(__name__)


class GetWRFSimulationHandler:
    """Handler for getting a single WRF simulation."""

    def __init__(self, repository: WRFSimulationRepository):
        self.repository = repository

    async def execute(self, query: GetWRFSimulationQuery) -> Optional[WRFSimulation]:
        """Execute the get simulation query."""
        return await self.repository.get_by_id(query.simulation_id)


class ListWRFSimulationsHandler:
    """Handler for listing WRF simulations."""

    def __init__(self, repository: WRFSimulationRepository):
        self.repository = repository

    async def execute(
        self, query: ListWRFSimulationsQuery
    ) -> List[WRFSimulation]:
        """Execute the list simulations query."""
        return await self.repository.list_all(
            status=query.status,
            skip=query.skip,
            limit=query.limit,
        )


class GetWRFSimulationStatusHandler:
    """Handler for getting simulation status."""

    def __init__(self, repository: WRFSimulationRepository):
        self.repository = repository

    async def execute(
        self, query: GetWRFSimulationStatusQuery
    ) -> Optional[dict]:
        """Execute the get status query."""
        simulation = await self.repository.get_by_id(query.simulation_id)
        if not simulation:
            return None

        return {
            "id": str(simulation.id),
            "name": simulation.name,
            "status": simulation.status.value,
            "progress_percent": simulation.progress_percent,
            "error_message": simulation.error_message,
            "elapsed_seconds": simulation.elapsed_seconds,
            "estimated_remaining_seconds": simulation.estimated_remaining_seconds,
            "created_at": simulation.created_at.isoformat(),
            "started_at": simulation.started_at.isoformat() if simulation.started_at else None,
            "completed_at": simulation.completed_at.isoformat() if simulation.completed_at else None,
        }


class GetRecommendedConfigHandler:
    """Handler for getting recommended WRF configuration."""

    def __init__(self):
        self.service = WRFSimulationService()

    async def execute(
        self, query: GetRecommendedConfigQuery
    ) -> dict:
        """Execute the get recommended config query."""
        config = self.service.recommend_configuration(
            center_lat=query.center_lat,
            center_lon=query.center_lon,
            region_radius_km=query.region_radius_km,
            available_memory_gb=query.available_memory_gb,
            max_runtime_hours=query.max_runtime_hours,
        )

        runtime_hours = self.service.estimate_runtime_hours(config)

        return {
            "config": config.to_dict(),
            "estimated_runtime_hours": round(runtime_hours, 2),
            "recommendation": self._generate_recommendation_text(config, runtime_hours),
        }

    def _generate_recommendation_text(self, config, runtime_hours: float) -> str:
        """Generate human-readable recommendation."""
        if runtime_hours < 1:
            runtime_text = f"less than an hour"
        elif runtime_hours < 4:
            runtime_text = f"approximately {runtime_hours:.1f} hours"
        else:
            runtime_text = f"approximately {runtime_hours:.1f} hours"

        return (
            f"Recommended configuration for your region: "
            f"{config.horizontal_resolution_km}km resolution with {config.vertical_levels} "
            f"vertical levels. Estimated runtime: {runtime_text}. "
            f"Memory requirement: {config.estimated_memory_gb:.1f}GB."
        )


class GetWRFForecastDataHandler:
    """Handler for getting forecast data."""

    def __init__(self, repository: WRFSimulationRepository):
        self.repository = repository

    async def execute(self, query: GetWRFForecastDataQuery) -> Optional[dict]:
        """Execute the get forecast data query."""
        simulation = await self.repository.get_by_id(query.simulation_id)
        if not simulation:
            return None

        if simulation.status != SimulationStatus.COMPLETED:
            return None

        # This would read actual data from WRF output files
        # For now, return metadata about available data
        return {
            "simulation_id": str(simulation.id),
            "variable": query.variable,
            "level": query.level,
            "bounding_box": simulation.config.bounding_box.to_dict(),
            "time_range": {
                "start": simulation.started_at.isoformat() if simulation.started_at else None,
                "end": simulation.completed_at.isoformat() if simulation.completed_at else None,
            },
            "output_files": simulation.wrf_output_files,
        }
