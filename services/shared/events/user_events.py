"""User domain events for the shared events library.

These events are published when user-related actions occur:
- UserRegistered: When a new user registers
- UserPasswordChanged: When a user changes their password
- UserLoggedIn: When a user successfully logs in

Other services can subscribe to these events for auditing,
notifications, or other cross-cutting concerns.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from .base_event import DomainEvent


@dataclass
class UserRegistered(DomainEvent):
    """Event published when a new user registers."""

    user_id: UUID = field(default_factory=uuid4)
    email: str = ""
    role: str = "PUBLIC"
    event_type: str = "user.registered"


@dataclass
class UserPasswordChanged(DomainEvent):
    """Event published when a user changes their password."""

    user_id: UUID = field(default_factory=uuid4)
    changed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = "user.password.changed"


@dataclass
class UserLoggedIn(DomainEvent):
    """Event published when a user successfully logs in."""

    user_id: UUID = field(default_factory=uuid4)
    email: str = ""
    logged_in_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: str = ""
    event_type: str = "user.logged_in"
