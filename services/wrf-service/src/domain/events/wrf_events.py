"""Domain events for WRF Service."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base class for domain events."""

    event_id: UUID
    occurred_at: datetime
    event_type: str

    def __post_init__(self):
        if self.event_id is None:
            self.event_id = uuid4()
        if self.occurred_at is None:
            self.occurred_at = datetime.utcnow()


@dataclass
class WRFSimulationCreated(DomainEvent):
    """Event fired when a new WRF simulation is created."""

    simulation_id: UUID
    name: str
    config: Dict[str, Any]
    event_type: str = "wrf.simulation.created"


@dataclass
class WRFSimulationStarted(DomainEvent):
    """Event fired when WRF simulation starts running."""

    simulation_id: UUID
    gfs_data_path: str
    event_type: str = "wrf.simulation.started"


@dataclass
class WRFSimulationCompleted(DomainEvent):
    """Event fired when WRF simulation completes successfully."""

    simulation_id: UUID
    output_file_path: str
    wrf_output_files: List[str]
    event_type: str = "wrf.simulation.completed"


@dataclass
class WRFSimulationFailed(DomainEvent):
    """Event fired when WRF simulation fails."""

    simulation_id: UUID
    error_message: str
    event_type: str = "wrf.simulation.failed"


@dataclass
class WeatherForecastGenerated(DomainEvent):
    """Event fired when weather forecast data is generated."""

    simulation_id: UUID
    forecast_id: UUID
    variable: str
    level: str
    file_path: str
    event_type: str = "wrf.forecast.generated"
