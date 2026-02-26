"""Command to resolve a violation."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class ResolveViolationCommand:
    """Data required to resolve an open violation."""

    violation_id: UUID
    notes: str = ""
    action_taken: str = ""
