"""Suspension entity for tracking factory operation suspensions.

Each time a factory is suspended a new ``Suspension`` record is created.
When the factory resumes, the matching active suspension is deactivated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Suspension:
    """Tracks an individual suspension period for a factory.

    Attributes
    ----------
    id:
        Unique identifier for this suspension record.
    factory_id:
        The factory that was suspended.
    reason:
        Human-readable explanation for the suspension.
    suspended_by:
        User ID of the authority who ordered the suspension.
    suspended_at:
        Timestamp when the suspension took effect.
    resumed_at:
        Timestamp when operations were resumed (``None`` while active).
    resumed_by:
        User ID of the authority who lifted the suspension.
    notes:
        Optional free-text notes added upon resumption.
    is_active:
        ``True`` while the suspension is in effect.
    """

    id: UUID = field(default_factory=uuid4)
    factory_id: UUID = None
    reason: str = ""
    suspended_by: UUID = None
    suspended_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resumed_at: Optional[datetime] = None
    resumed_by: Optional[UUID] = None
    notes: str = ""
    is_active: bool = True

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------
    def deactivate(self, resumed_by: UUID, notes: str = "") -> None:
        """Mark this suspension as lifted.

        Raises ``ValueError`` if the suspension is not currently active.
        """
        if not self.is_active:
            raise ValueError("Suspension is already inactive")

        self.is_active = False
        self.resumed_at = datetime.now(timezone.utc)
        self.resumed_by = resumed_by
        self.notes = notes

    @property
    def duration_seconds(self) -> Optional[float]:
        """Return the suspension duration in seconds, or ``None`` if still active."""
        if self.resumed_at is None:
            return None
        return (self.resumed_at - self.suspended_at).total_seconds()

    # ------------------------------------------------------------------
    # Factory method
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        factory_id: UUID,
        reason: str,
        suspended_by: UUID,
    ) -> Suspension:
        """Create a new active suspension."""
        return cls(
            id=uuid4(),
            factory_id=factory_id,
            reason=reason,
            suspended_by=suspended_by,
        )
