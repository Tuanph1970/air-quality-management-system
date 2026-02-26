"""Factory domain events — re-exported from the shared event library.

The canonical event definitions live in ``shared.events.factory_events``
so that both producers (this service) and consumers (other services) use
the same classes.  This module simply re-exports them for convenience
within the factory-service codebase.
"""
from shared.events.factory_events import (  # noqa: F401
    FactoryCreated,
    FactoryUpdated,
    FactoryStatusChanged,
    FactorySuspended,
    FactoryResumed,
)

__all__ = [
    "FactoryCreated",
    "FactoryUpdated",
    "FactoryStatusChanged",
    "FactorySuspended",
    "FactoryResumed",
]
