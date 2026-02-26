"""Command to suspend a factory."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class SuspendFactoryCommand:
    factory_id: UUID
    reason: str
    suspended_by: UUID
