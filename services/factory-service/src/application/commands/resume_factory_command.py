"""Command to resume a suspended factory."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class ResumeFactoryCommand:
    factory_id: UUID
    resumed_by: UUID
