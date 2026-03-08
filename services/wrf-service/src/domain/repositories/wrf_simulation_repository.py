"""Repositories for WRF Service."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.wrf_simulation import WRFSimulation, SimulationStatus


class WRFSimulationRepository(ABC):
    """Repository interface for WRF simulations."""

    @abstractmethod
    async def get_by_id(self, simulation_id: UUID) -> Optional[WRFSimulation]:
        """Get simulation by ID."""
        pass

    @abstractmethod
    async def list_all(
        self,
        status: Optional[SimulationStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[WRFSimulation]:
        """List simulations with optional filtering."""
        pass

    @abstractmethod
    async def save(self, simulation: WRFSimulation) -> WRFSimulation:
        """Save or update a simulation."""
        pass

    @abstractmethod
    async def delete(self, simulation_id: UUID) -> bool:
        """Delete a simulation."""
        pass

    @abstractmethod
    async def get_active_simulations(self) -> List[WRFSimulation]:
        """Get all non-completed simulations."""
        pass
