"""Repository implementation for WRF simulations."""
import json
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.wrf_simulation import (
    WRFSimulation,
    SimulationStatus,
)
from ...domain.repositories.wrf_simulation_repository import (
    WRFSimulationRepository,
)
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
from .models import WRFSimulationModel

logger = logging.getLogger(__name__)


class SQLAlchemyWRFSimulationRepository(WRFSimulationRepository):
    """SQLAlchemy implementation of WRF simulation repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, simulation_id: UUID) -> Optional[WRFSimulation]:
        """Get simulation by ID."""
        result = await self.session.execute(
            select(WRFSimulationModel).where(
                WRFSimulationModel.id == simulation_id
            )
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def list_all(
        self,
        status: Optional[SimulationStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[WRFSimulation]:
        """List simulations with optional filtering."""
        query = select(WRFSimulationModel)

        if status:
            query = query.where(WRFSimulationModel.status == status.value)

        query = query.order_by(WRFSimulationModel.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def save(self, simulation: WRFSimulation) -> WRFSimulation:
        """Save or update a simulation."""
        model = await self._get_or_create_model(simulation)

        # Update fields
        model.name = simulation.name
        model.status = simulation.status.value
        model.progress_percent = simulation.progress_percent
        model.error_message = simulation.error_message
        model.config_json = json.dumps(simulation.config.to_dict())
        model.output_file_path = simulation.output_file_path
        model.gfs_data_path = simulation.gfs_data_path
        model.wrf_output_files = (
            json.dumps(simulation.wrf_output_files)
            if simulation.wrf_output_files
            else None
        )
        model.started_at = simulation.started_at
        model.completed_at = simulation.completed_at

        await self.session.merge(model)
        await self.session.flush()

        logger.debug(f"Saved simulation {simulation.id}")

        return simulation

    async def delete(self, simulation_id: UUID) -> bool:
        """Delete a simulation."""
        result = await self.session.execute(
            select(WRFSimulationModel).where(
                WRFSimulationModel.id == simulation_id
            )
        )
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.flush()

        logger.info(f"Deleted simulation {simulation_id}")
        return True

    async def get_active_simulations(self) -> List[WRFSimulation]:
        """Get all non-completed simulations."""
        active_statuses = [
            SimulationStatus.PENDING.value,
            SimulationStatus.DOWNLOADING_DATA.value,
            SimulationStatus.PREPROCESSING.value,
            SimulationStatus.RUNNING.value,
            SimulationStatus.POST_PROCESSING.value,
        ]

        result = await self.session.execute(
            select(WRFSimulationModel).where(
                WRFSimulationModel.status.in_(active_statuses)
            )
        )
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def _get_or_create_model(
        self, simulation: WRFSimulation
    ) -> WRFSimulationModel:
        """Get existing model or create new one."""
        result = await self.session.execute(
            select(WRFSimulationModel).where(
                WRFSimulationModel.id == simulation.id
            )
        )
        model = result.scalar_one_or_none()

        if not model:
            model = WRFSimulationModel(
                id=simulation.id,
                name=simulation.name,
            )

        return model

    def _to_entity(self, model: WRFSimulationModel) -> WRFSimulation:
        """Convert SQLAlchemy model to domain entity."""
        config_dict = (
            json.loads(model.config_json)
            if model.config_json
            else {}
        )

        # Reconstruct WRFConfig from JSON
        config = self._config_from_dict(config_dict)

        wrf_output_files = (
            json.loads(model.wrf_output_files)
            if model.wrf_output_files
            else []
        )

        return WRFSimulation(
            id=model.id,
            name=model.name,
            config=config,
            status=SimulationStatus(model.status),
            progress_percent=model.progress_percent,
            error_message=model.error_message,
            output_file_path=model.output_file_path,
            gfs_data_path=model.gfs_data_path,
            wrf_output_files=wrf_output_files,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )

    def _config_from_dict(self, config_dict: dict) -> WRFConfig:
        """Reconstruct WRFConfig from dictionary."""
        bbox_dict = config_dict.get("bounding_box", {})
        bounding_box = BoundingBox(
            north=bbox_dict.get("north", 0),
            south=bbox_dict.get("south", 0),
            east=bbox_dict.get("east", 0),
            west=bbox_dict.get("west", 0),
        )

        physics_dict = config_dict.get("physics_options", {})
        physics_options = PhysicsOptions(
            microphysics=MicrophysicsScheme(
                physics_dict.get("microphysics", "wsmd6")
            ),
            longwave_radiation=LongwaveRadiationScheme(
                physics_dict.get("longwave_radiation", "rrtm")
            ),
            shortwave_radiation=ShortwaveRadiationScheme(
                physics_dict.get("shortwave_radiation", "dudhia")
            ),
            land_surface=LandSurfaceModel(
                physics_dict.get("land_surface", "noah")
            ),
            pbl_scheme=PlanetaryBoundaryLayerScheme(
                physics_dict.get("pbl_scheme", "ysu")
            ),
        )

        return WRFConfig(
            bounding_box=bounding_box,
            horizontal_resolution_km=config_dict.get(
                "horizontal_resolution_km", 9.0
            ),
            vertical_levels=config_dict.get("vertical_levels", 30),
            simulation_hours=config_dict.get("simulation_hours", 48),
            physics_options=physics_options,
            output_interval_hours=config_dict.get("output_interval_hours", 1),
            start_date=config_dict.get("start_date"),
        )
