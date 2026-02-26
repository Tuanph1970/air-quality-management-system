"""Command to resolve a violation."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class ResolveViolationCommand:
    violation_id: UUID
    resolved_by: UUID
