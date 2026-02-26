"""Notification domain service."""
from abc import ABC, abstractmethod


class NotificationService(ABC):
    """Abstract notification service."""

    @abstractmethod
    async def send_alert(self, violation) -> None:
        pass
