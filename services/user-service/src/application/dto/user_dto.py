"""User data transfer objects."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ...domain.entities.user import User


@dataclass
class UserDTO:
    """Read-only projection of a User entity for the interface layer.

    Does not include sensitive data like password_hash.
    """

    id: UUID
    email: str
    full_name: str
    role: str
    organization: Optional[str]
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    @classmethod
    def from_entity(cls, entity: User) -> UserDTO:
        """Map a domain entity to a DTO."""
        return cls(
            id=entity.id,
            email=str(entity.email),
            full_name=entity.full_name,
            role=entity.role.value,
            organization=entity.organization,
            is_active=entity.is_active,
            created_at=entity.created_at,
            last_login_at=entity.last_login_at,
        )


@dataclass
class TokenResponse:
    """JWT token response for authentication.

    Attributes
    ----------
    access_token:
        JWT access token
    token_type:
        Token type (always "bearer")
    expires_in:
        Token expiration time in seconds
    user:
        User information
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour default
    user: Optional[UserDTO] = None


@dataclass
class RefreshTokenRequest:
    """Request to refresh an access token.

    Attributes
    ----------
    refresh_token:
        Refresh token to exchange for new access token
    """

    refresh_token: str
