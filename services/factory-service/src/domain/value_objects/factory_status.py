"""Factory status enum."""
from enum import Enum


class FactoryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SUSPENDED = "SUSPENDED"
