"""Violation entity."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Violation:
    """Violation Entity."""

    id: UUID = field(default_factory=uuid4)
    factory_id: UUID = None
    pollutant: str = ""
    measured_value: float = 0.0
    threshold: float = 0.0
    severity: str = "LOW"
    status: str = "OPEN"
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
