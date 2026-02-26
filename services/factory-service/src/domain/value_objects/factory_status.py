"""Factory operational status enum.

Represents the lifecycle states a factory can be in.  Transitions are
enforced by the Factory entity's business methods.
"""
from enum import Enum


class FactoryStatus(str, Enum):
    """Operational status of a factory.

    Transition rules (enforced in Factory entity):
        ACTIVE  -> WARNING | CRITICAL | SUSPENDED | CLOSED
        WARNING -> ACTIVE | CRITICAL | SUSPENDED | CLOSED
        CRITICAL -> ACTIVE | WARNING | SUSPENDED | CLOSED
        SUSPENDED -> ACTIVE  (via resume only)
        CLOSED -> (terminal — no transitions out)
    """

    ACTIVE = "ACTIVE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"

    @property
    def is_operational(self) -> bool:
        """Return ``True`` if the factory can operate (not suspended/closed)."""
        return self in (self.ACTIVE, self.WARNING, self.CRITICAL)

    @property
    def is_terminal(self) -> bool:
        """Return ``True`` if this is a terminal state."""
        return self == self.CLOSED
