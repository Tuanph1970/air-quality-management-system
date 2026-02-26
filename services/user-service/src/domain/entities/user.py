"""User entity."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID, uuid4


@dataclass
class User:
    """User Entity."""

    id: UUID = field(default_factory=uuid4)
    email: str = ""
    hashed_password: str = ""
    full_name: str = ""
    role: str = "viewer"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _events: List = field(default_factory=list, repr=False)

    def collect_events(self) -> List:
        events = self._events.copy()
        self._events.clear()
        return events
