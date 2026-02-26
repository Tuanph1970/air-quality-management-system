"""Query to get factory emission data."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class GetFactoryEmissionsQuery:
    factory_id: UUID
