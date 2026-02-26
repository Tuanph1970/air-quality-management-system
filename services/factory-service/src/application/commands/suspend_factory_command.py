"""Command to suspend a factory."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SuspendFactoryCommand:
    """Immutable command to suspend factory operations."""

    factory_id: UUID
    reason: str
    suspended_by: UUID

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid."""
        if not self.reason or not self.reason.strip():
            raise ValueError("Suspension reason is required")
