"""Suspension entity for factory operation suspensions."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Suspension:
    """Suspension Entity."""

    id: UUID = field(default_factory=uuid4)
    factory_id: UUID = None
    reason: str = ""
    suspended_by: UUID = None
    suspended_at: datetime = field(default_factory=datetime.utcnow)
    resumed_at: Optional[datetime] = None
    is_active: bool = True
