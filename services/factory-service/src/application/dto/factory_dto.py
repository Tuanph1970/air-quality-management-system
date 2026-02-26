"""Factory data transfer objects."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID


@dataclass
class FactoryDTO:
    id: UUID
    name: str
    registration_number: str
    industry_type: str
    latitude: float
    longitude: float
    max_emissions: Dict
    operational_status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity) -> "FactoryDTO":
        pass
