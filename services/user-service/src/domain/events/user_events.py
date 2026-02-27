"""User domain events (re-exported from shared library).

The canonical event definitions live in ``shared.events.user_events``
so that other bounded contexts can import them without depending on
this service. This module simply re-exports them for convenience.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from shared.events.user_events import (  # noqa: F401
    UserRegistered,
    UserPasswordChanged,
    UserLoggedIn,
)

__all__ = [
    "UserRegistered",
    "UserPasswordChanged",
    "UserLoggedIn",
]
