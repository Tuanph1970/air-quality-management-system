"""Notification service protocol (port interface).

Defines the contract for sending violation notifications.  The domain
layer declares *what* notifications to send; the infrastructure layer
provides *how* (email, SMS, push, etc.).

Uses ``typing.Protocol`` for structural subtyping — any class that
implements the required methods satisfies the protocol without explicit
inheritance.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..entities.violation import Violation


@runtime_checkable
class NotificationService(Protocol):
    """Port interface for violation notification delivery.

    Infrastructure implementations might include:
    - ``EmailNotificationService`` (SMTP / SES)
    - ``SMSNotificationService`` (Twilio / SNS)
    - ``CompositeNotificationService`` (routes to multiple channels)
    """

    async def send_email(self, violation: Violation) -> None:
        """Send an email notification about a violation.

        Parameters
        ----------
        violation:
            The violation to notify about.
        """
        ...

    async def send_sms(self, violation: Violation) -> None:
        """Send an SMS notification about a violation.

        Parameters
        ----------
        violation:
            The violation to notify about.
        """
        ...
