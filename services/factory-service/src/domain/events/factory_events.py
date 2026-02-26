"""Factory domain events."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class FactoryCreated:
    factory_id: UUID = None
    name: str = ""


@dataclass
class FactoryStatusChanged:
    factory_id: UUID = None
    old_status: str = ""
    new_status: str = ""
    reason: str = ""


@dataclass
class FactorySuspended:
    factory_id: UUID = None
    reason: str = ""
    suspended_by: UUID = None
