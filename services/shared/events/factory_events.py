"""Factory domain events shared across services.

Published by the Factory Service and consumed by any service that needs
to react to factory lifecycle changes (Alert Service, Air Quality Service, etc.).
"""
from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import UUID

from .base_event import DomainEvent


@dataclass
class FactoryCreated(DomainEvent):
    """A new factory has been registered in the system."""

    factory_id: UUID = None
    name: str = ""
    registration_number: str = ""
    industry_type: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    max_emissions: Dict = field(default_factory=dict)
    event_type: str = "factory.created"


@dataclass
class FactoryUpdated(DomainEvent):
    """Factory details have been modified."""

    factory_id: UUID = None
    updated_fields: Dict = field(default_factory=dict)
    event_type: str = "factory.updated"


@dataclass
class FactoryStatusChanged(DomainEvent):
    """Factory operational status transitioned (e.g. ACTIVE -> WARNING)."""

    factory_id: UUID = None
    old_status: str = ""
    new_status: str = ""
    reason: str = ""
    event_type: str = "factory.status.changed"


@dataclass
class FactorySuspended(DomainEvent):
    """Factory operations have been suspended by an authority."""

    factory_id: UUID = None
    reason: str = ""
    suspended_by: UUID = None
    event_type: str = "factory.suspended"


@dataclass
class FactoryResumed(DomainEvent):
    """A previously suspended factory has resumed operations."""

    factory_id: UUID = None
    resumed_by: UUID = None
    notes: str = ""
    event_type: str = "factory.resumed"
