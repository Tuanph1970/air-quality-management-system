"""Alert domain events (re-exported from shared library).

The canonical event definitions live in ``shared.events.alert_events``
so that other bounded contexts can import them without depending on this
service.  This module simply re-exports them for convenience within the
alert service codebase.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from shared.events.alert_events import (  # noqa: F401
    AlertConfigUpdated,
    ViolationDetected,
    ViolationResolved,
)

__all__ = [
    "ViolationDetected",
    "ViolationResolved",
    "AlertConfigUpdated",
]
