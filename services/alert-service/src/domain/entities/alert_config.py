"""Alert configuration entity."""
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class AlertConfig:
    """Alert Configuration Entity."""

    id: UUID = field(default_factory=uuid4)
    pollutant: str = ""
    threshold: float = 0.0
    severity: str = "LOW"
    is_active: bool = True
