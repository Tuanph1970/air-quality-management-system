"""Event publisher interface (port)."""
from abc import ABC, abstractmethod


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event) -> None:
        pass
