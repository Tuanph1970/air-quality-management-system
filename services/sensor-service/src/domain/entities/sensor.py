"""Sensor entity."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class Sensor:
    """Sensor Entity - has identity and lifecycle."""

    id: UUID = field(default_factory=uuid4)
    factory_id: UUID = None
    sensor_type: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    status: str = "ACTIVE"
    last_calibration: Optional[datetime] = None
    installed_at: datetime = field(default_factory=datetime.utcnow)
    _events: List = field(default_factory=list, repr=False)

    def collect_events(self) -> List:
        events = self._events.copy()
        self._events.clear()
        return events
