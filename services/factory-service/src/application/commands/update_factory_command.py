"""Command to update an existing factory."""
from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID


@dataclass
class UpdateFactoryCommand:
    factory_id: UUID
    name: Optional[str] = None
    industry_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    emission_limits: Optional[Dict] = None
