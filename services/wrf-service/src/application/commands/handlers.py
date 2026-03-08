"""Command handlers for WRF Service."""
import logging
from typing import Optional
from uuid import UUID

from ...domain.entities.wrf_simulation import WRFSimulation, SimulationStatus
from ...domain.repositories.wrf_simulation_repository import WRFSimulationRepository
from ...domain.services.wrf_simulation_service import WRFSimulationService
from ...infrastructure.external.gfs_data_downloader import GFSDataDownloader
from ...infrastructure.wrf.wrf_model_runner import WRFModelRunner
from .wrf_commands import (
    CreateWRFSimulationCommand,
    StartWRFSimulationCommand,
    CancelWRFSimulationCommand,
    DeleteWRFSimulationCommand,
)

logger = logging.getLogger(__name__)


class CreateWRFSimulationHandler:
    """Handler for creating WRF simulations."""

    def __init__(self, repository: WRFSimulationRepository):
        self.repository = repository
        self.validation_service = WRFSimulationService()

    async def execute(self, command: CreateWRFSimulationCommand) -> WRFSimulation:
        """Execute the create simulation command."""
        # Convert command to config
        config = command.to_config()

        # Validate configuration
        is_valid, error_message = self.validation_service.validate_simulation_config(
            config
        )
        if not is_valid:
            raise ValueError(error_message)

        # Create simulation entity
        simulation = WRFSimulation.create(name=command.name, config=config)

        # Save to repository
        return await self.repository.save(simulation)


class StartWRFSimulationHandler:
    """Handler for starting WRF simulations."""

    def __init__(
        self,
        repository: WRFSimulationRepository,
        gfs_downloader: GFSDataDownloader,
        wrf_runner: WRFModelRunner,
    ):
        self.repository = repository
        self.gfs_downloader = gfs_downloader
        self.wrf_runner = wrf_runner

    async def execute(self, command: StartWRFSimulationCommand) -> WRFSimulation:
        """Execute the start simulation command."""
        # Get simulation
        simulation = await self.repository.get_by_id(command.simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {command.simulation_id} not found")

        if simulation.status != SimulationStatus.PENDING:
            raise ValueError(f"Cannot start simulation in status {simulation.status}")

        try:
            # Download GFS data
            simulation.update_progress(
                SimulationStatus.DOWNLOADING_DATA,
                5,
                "Downloading GFS boundary conditions...",
            )
            await self.repository.save(simulation)

            gfs_data_path = await self.gfs_downloader.download(
                simulation.config, simulation.id
            )

            # Start WRF simulation
            simulation.start(gfs_data_path)
            await self.repository.save(simulation)

            # Run WRF model (this will be a long-running process)
            await self._run_wrf_simulation(simulation)

            return simulation

        except Exception as e:
            logger.exception(f"Failed to start simulation: {e}")
            simulation.mark_failed(str(e))
            await self.repository.save(simulation)
            raise

    async def _run_wrf_simulation(self, simulation: WRFSimulation) -> None:
        """Run the WRF model with progress updates."""
        try:
            # Preprocessing
            simulation.update_progress(
                SimulationStatus.PREPROCESSING,
                15,
                "Running WPS preprocessing...",
            )
            await self.repository.save(simulation)

            await self.wrf_runner.run_preprocessing(simulation)

            # WRF Model execution
            simulation.update_progress(
                SimulationStatus.RUNNING,
                30,
                "Running WRF model...",
            )
            await self.repository.save(simulation)

            async def progress_callback(progress: int, message: str):
                simulation.update_progress(
                    SimulationStatus.RUNNING,
                    30 + int(progress * 0.6),
                    message,
                )
                await self.repository.save(simulation)

            output_files = await self.wrf_runner.run_simulation(
                simulation, progress_callback
            )

            # Post-processing
            simulation.update_progress(
                SimulationStatus.POST_PROCESSING,
                90,
                "Post-processing output...",
            )
            await self.repository.save(simulation)

            await self.wrf_runner.post_process(simulation)

            # Mark completed
            output_path = f"/app/data/simulations/{simulation.id}"
            simulation.mark_completed(output_path, output_files)
            await self.repository.save(simulation)

        except Exception as e:
            logger.exception(f"WRF simulation failed: {e}")
            simulation.mark_failed(str(e))
            await self.repository.save(simulation)
            raise


class CancelWRFSimulationHandler:
    """Handler for cancelling WRF simulations."""

    def __init__(self, repository: WRFSimulationRepository):
        self.repository = repository

    async def execute(self, command: CancelWRFSimulationCommand) -> WRFSimulation:
        """Execute the cancel simulation command."""
        simulation = await self.repository.get_by_id(command.simulation_id)
        if not simulation:
            raise ValueError(f"Simulation {command.simulation_id} not found")

        simulation.cancel()
        return await self.repository.save(simulation)


class DeleteWRFSimulationHandler:
    """Handler for deleting WRF simulations."""

    def __init__(self, repository: WRFSimulationRepository):
        self.repository = repository

    async def execute(self, command: DeleteWRFSimulationCommand) -> bool:
        """Execute the delete simulation command."""
        return await self.repository.delete(command.simulation_id)
