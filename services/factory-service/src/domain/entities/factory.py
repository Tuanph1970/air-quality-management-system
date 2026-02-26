"""Factory entity with identity and lifecycle."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID, uuid4


@dataclass
class Factory:
    """Factory Entity - has identity and lifecycle."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    registration_number: str = ""
    industry_type: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    max_emissions: dict = field(default_factory=dict)
    operational_status: str = "ACTIVE"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _events: List = field(default_factory=list, repr=False)

    def collect_events(self) -> List:
        events = self._events.copy()
        self._events.clear()
        return events
