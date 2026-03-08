"""WRF Application Service - orchestrates use cases."""
import logging
from typing import List, Optional
from uuid import UUID

from ...domain.entities.wrf_simulation import WRFSimulation, SimulationStatus
from ...domain.repositories.wrf_simulation_repository import WRFSimulationRepository
from ...domain.services.wrf_simulation_service import WRFSimulationService
from ...infrastructure.external.gfs_data_downloader import GFSDataDownloader
from ...infrastructure.wrf.wrf_model_runner import WRFModelRunner
from ..commands.wrf_commands import (
    CreateWRFSimulationCommand,
    StartWRFSimulationCommand,
    CancelWRFSimulationCommand,
    DeleteWRFSimulationCommand,
)
from ..commands.handlers import (
    CreateWRFSimulationHandler,
    StartWRFSimulationHandler,
    CancelWRFSimulationHandler,
    DeleteWRFSimulationHandler,
)
from ..queries.wrf_queries import (
    GetWRFSimulationQuery,
    ListWRFSimulationsQuery,
    GetWRFSimulationStatusQuery,
    GetRecommendedConfigQuery,
)
from ..queries.handlers import (
    GetWRFSimulationHandler,
    ListWRFSimulationsHandler,
    GetWRFSimulationStatusHandler,
    GetRecommendedConfigHandler,
)

logger = logging.getLogger(__name__)


class WRFApplicationService:
    """Application service for WRF simulations.

    This service orchestrates the use cases for WRF simulation management,
    coordinating between commands, queries, and infrastructure.
    """

    def __init__(
        self,
        repository: WRFSimulationRepository,
        gfs_downloader: GFSDataDownloader,
        wrf_runner: WRFModelRunner,
    ):
        self.repository = repository
        self.gfs_downloader = gfs_downloader
        self.wrf_runner = wrf_runner

        # Initialize command handlers
        self.create_handler = CreateWRFSimulationHandler(repository)
        self.start_handler = StartWRFSimulationHandler(
            repository, gfs_downloader, wrf_runner
        )
        self.cancel_handler = CancelWRFSimulationHandler(repository)
        self.delete_handler = DeleteWRFSimulationHandler(repository)

        # Initialize query handlers
        self.get_handler = GetWRFSimulationHandler(repository)
        self.list_handler = ListWRFSimulationsHandler(repository)
        self.status_handler = GetWRFSimulationStatusHandler(repository)
        self.recommend_handler = GetRecommendedConfigHandler()

    # Command methods (write operations)

    async def create_simulation(
        self,
        name: str,
        north: float,
        south: float,
        east: float,
        west: float,
        horizontal_resolution_km: float,
        vertical_levels: int,
        simulation_hours: int,
        output_interval_hours: int = 1,
        start_date: Optional[str] = None,
        physics_options: Optional[dict] = None,
    ) -> WRFSimulation:
        """Create a new WRF simulation."""
        command = CreateWRFSimulationCommand(
            name=name,
            north=north,
            south=south,
            east=east,
            west=west,
            horizontal_resolution_km=horizontal_resolution_km,
            vertical_levels=vertical_levels,
            simulation_hours=simulation_hours,
            output_interval_hours=output_interval_hours,
            start_date=start_date,
            **(physics_options or {}),
        )
        return await self.create_handler.execute(command)

    async def start_simulation(self, simulation_id: UUID) -> WRFSimulation:
        """Start a WRF simulation."""
        command = StartWRFSimulationCommand(simulation_id=simulation_id)
        return await self.start_handler.execute(command)

    async def cancel_simulation(self, simulation_id: UUID) -> WRFSimulation:
        """Cancel a running WRF simulation."""
        command = CancelWRFSimulationCommand(simulation_id=simulation_id)
        return await self.cancel_handler.execute(command)

    async def delete_simulation(self, simulation_id: UUID) -> bool:
        """Delete a WRF simulation."""
        command = DeleteWRFSimulationCommand(simulation_id=simulation_id)
        return await self.delete_handler.execute(command)

    # Query methods (read operations)

    async def get_simulation(self, simulation_id: UUID) -> Optional[WRFSimulation]:
        """Get a WRF simulation by ID."""
        query = GetWRFSimulationQuery(simulation_id=simulation_id)
        return await self.get_handler.execute(query)

    async def list_simulations(
        self,
        status: Optional[SimulationStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[WRFSimulation]:
        """List WRF simulations with optional filtering."""
        query = ListWRFSimulationsQuery(
            status=status,
            skip=skip,
            limit=limit,
        )
        return await self.list_handler.execute(query)

    async def get_simulation_status(
        self, simulation_id: UUID
    ) -> Optional[dict]:
        """Get current status of a simulation."""
        query = GetWRFSimulationStatusQuery(simulation_id=simulation_id)
        return await self.status_handler.execute(query)

    async def get_recommended_config(
        self,
        center_lat: float,
        center_lon: float,
        region_radius_km: float,
        available_memory_gb: float = 16.0,
        max_runtime_hours: float = 4.0,
    ) -> dict:
        """Get recommended WRF configuration for a region."""
        query = GetRecommendedConfigQuery(
            center_lat=center_lat,
            center_lon=center_lon,
            region_radius_km=region_radius_km,
            available_memory_gb=available_memory_gb,
            max_runtime_hours=max_runtime_hours,
        )
        return await self.recommend_handler.execute(query)
