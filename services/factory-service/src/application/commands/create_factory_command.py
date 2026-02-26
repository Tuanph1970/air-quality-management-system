"""Command to create a new factory."""
from dataclasses import dataclass
from typing import Dict


@dataclass
class CreateFactoryCommand:
    name: str
    registration_number: str
    industry_type: str
    latitude: float
    longitude: float
    emission_limits: Dict
