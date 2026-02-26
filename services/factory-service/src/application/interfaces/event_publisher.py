"""Event publisher interface (port)."""
from abc import ABC, abstractmethod


class EventPublisher(ABC):
    """Abstract event publisher interface."""

    @abstractmethod
    async def publish(self, event) -> None:
        pass
