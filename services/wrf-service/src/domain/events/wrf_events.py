"""Domain events for WRF Service."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base class for domain events."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_type: str = ""


@dataclass
class WRFSimulationCreated(DomainEvent):
    """Event fired when a new WRF simulation is created."""

    simulation_id: Optional[UUID] = None
    name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    event_type: str = "wrf.simulation.created"


@dataclass
class WRFSimulationStarted(DomainEvent):
    """Event fired when WRF simulation starts running."""

    simulation_id: Optional[UUID] = None
    gfs_data_path: str = ""
    event_type: str = "wrf.simulation.started"


@dataclass
class WRFSimulationCompleted(DomainEvent):
    """Event fired when WRF simulation completes successfully."""

    simulation_id: Optional[UUID] = None
    output_file_path: str = ""
    wrf_output_files: List[str] = field(default_factory=list)
    event_type: str = "wrf.simulation.completed"


@dataclass
class WRFSimulationFailed(DomainEvent):
    """Event fired when WRF simulation fails."""

    simulation_id: Optional[UUID] = None
    error_message: str = ""
    event_type: str = "wrf.simulation.failed"


@dataclass
class WeatherForecastGenerated(DomainEvent):
    """Event fired when weather forecast data is generated."""

    simulation_id: Optional[UUID] = None
    forecast_id: Optional[UUID] = None
    variable: str = ""
    level: str = ""
    file_path: str = ""
    event_type: str = "wrf.forecast.generated"
