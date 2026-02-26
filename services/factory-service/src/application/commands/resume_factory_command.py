"""Command to resume a suspended factory."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ResumeFactoryCommand:
    """Immutable command to resume a previously suspended factory."""

    factory_id: UUID
    resumed_by: UUID
    notes: str = ""
