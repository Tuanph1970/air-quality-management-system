"""WRF Simulation entity."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from ..value_objects.wrf_config import WRFConfig
from ..events.wrf_events import (
    WRFSimulationCreated,
    WRFSimulationStarted,
    WRFSimulationCompleted,
    WRFSimulationFailed,
)


class SimulationStatus(Enum):
    """Status of WRF simulation."""

    PENDING = "pending"
    DOWNLOADING_DATA = "downloading_data"
    PREPROCESSING = "preprocessing"
    RUNNING = "running"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WRFSimulation:
    """WRF Simulation Aggregate Root - represents a weather forecast simulation."""

    id: UUID
    name: str
    config: WRFConfig
    status: SimulationStatus = SimulationStatus.PENDING
    progress_percent: int = 0
    error_message: Optional[str] = None
    output_file_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    gfs_data_path: Optional[str] = None
    wrf_output_files: List[str] = field(default_factory=list)

    _events: list = field(default_factory=list, repr=False)

    @classmethod
    def create(
        cls,
        name: str,
        config: WRFConfig,
        simulation_id: Optional[UUID] = None,
    ) -> "WRFSimulation":
        """Factory method to create a new WRF simulation."""
        simulation = cls(
            id=simulation_id or uuid4(),
            name=name,
            config=config,
        )
        simulation._events.append(
            WRFSimulationCreated(
                simulation_id=simulation.id,
                name=name,
                config=config.to_dict(),
            )
        )
        return simulation

    def start(self, gfs_data_path: str) -> None:
        """Mark simulation as started with GFS data available."""
        if self.status != SimulationStatus.PENDING:
            raise ValueError(f"Cannot start simulation in status {self.status}")

        self.status = SimulationStatus.DOWNLOADING_DATA
        self.started_at = datetime.utcnow()
        self.gfs_data_path = gfs_data_path
        self._events.append(
            WRFSimulationStarted(
                simulation_id=self.id,
                gfs_data_path=gfs_data_path,
            )
        )

    def update_progress(
        self, status: SimulationStatus, progress_percent: int, message: Optional[str] = None
    ) -> None:
        """Update simulation progress."""
        self.status = status
        self.progress_percent = min(100, max(0, progress_percent))
        if message and status == SimulationStatus.FAILED:
            self.error_message = message

    def mark_completed(self, output_file_path: str, wrf_output_files: List[str]) -> None:
        """Mark simulation as completed."""
        self.status = SimulationStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100
        self.output_file_path = output_file_path
        self.wrf_output_files = wrf_output_files
        self._events.append(
            WRFSimulationCompleted(
                simulation_id=self.id,
                output_file_path=output_file_path,
                wrf_output_files=wrf_output_files,
            )
        )

    def mark_failed(self, error_message: str) -> None:
        """Mark simulation as failed."""
        self.status = SimulationStatus.FAILED
        self.error_message = error_message
        self._events.append(
            WRFSimulationFailed(
                simulation_id=self.id,
                error_message=error_message,
            )
        )

    def cancel(self) -> None:
        """Cancel the simulation."""
        if self.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]:
            raise ValueError(f"Cannot cancel simulation in status {self.status}")

        self.status = SimulationStatus.CANCELLED
        self._events.append(
            WRFSimulationFailed(
                simulation_id=self.id,
                error_message="Simulation cancelled by user",
            )
        )

    @property
    def elapsed_seconds(self) -> Optional[float]:
        """Calculate elapsed time since start."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    @property
    def estimated_remaining_seconds(self) -> Optional[float]:
        """Estimate remaining time based on progress."""
        if self.status == SimulationStatus.COMPLETED:
            return 0
        if not self.elapsed_seconds or self.progress_percent == 0:
            return None

        total_estimated = self.elapsed_seconds / (self.progress_percent / 100)
        return total_estimated - self.elapsed_seconds

    def collect_events(self) -> list:
        """Collect and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "config": self.config.to_dict(),
            "error_message": self.error_message,
            "output_file_path": self.output_file_path,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
            "wrf_output_files": self.wrf_output_files,
        }
