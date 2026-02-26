"""Event publisher interface (port).

Uses ``typing.Protocol`` for structural subtyping — any class that
implements ``publish()`` satisfies the contract without explicit
inheritance.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from shared.events.base_event import DomainEvent


@runtime_checkable
class EventPublisher(Protocol):
    """Port interface for publishing domain events to the message broker."""

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        ...
