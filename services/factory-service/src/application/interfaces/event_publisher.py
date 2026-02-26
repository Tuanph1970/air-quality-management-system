"""Event publisher interface (port).

Defines the contract that infrastructure-layer publishers must implement.
Uses ``typing.Protocol`` for structural subtyping — concrete classes do
**not** need to inherit from this protocol, they just need to have a
matching ``publish`` method.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from shared.events.base_event import DomainEvent


@runtime_checkable
class EventPublisher(Protocol):
    """Structural interface for publishing domain events.

    Any object with an ``async def publish(self, event: DomainEvent) -> None``
    method satisfies this protocol.
    """

    async def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event to the message broker."""
        ...
