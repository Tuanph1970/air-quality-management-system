"""User data transfer objects."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class UserDTO:
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_entity(cls, entity) -> "UserDTO":
        pass


@dataclass
class TokenDTO:
    access_token: str
    token_type: str = "bearer"
