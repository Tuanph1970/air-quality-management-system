"""Query to get a factory by ID."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class GetFactoryQuery:
    factory_id: UUID
