"""Role entity."""
from dataclasses import dataclass, field
from typing import List
from uuid import UUID, uuid4


@dataclass
class Role:
    """Role Entity."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    permissions: List[str] = field(default_factory=list)
