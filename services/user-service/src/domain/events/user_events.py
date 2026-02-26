"""User domain events."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class UserRegistered:
    user_id: UUID = None
    email: str = ""


@dataclass
class UserLoggedIn:
    user_id: UUID = None


@dataclass
class UserDeactivated:
    user_id: UUID = None
