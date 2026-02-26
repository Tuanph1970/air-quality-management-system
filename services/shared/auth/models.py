"""Auth data models used across all services.

These are plain dataclasses (not Pydantic) so the shared library stays
free of framework coupling.  Services can convert them to Pydantic
models in their own interface layer if needed.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class TokenPayload:
    """The raw claims extracted from a decoded JWT.

    Maps 1-to-1 with what ``jwt_handler.decode_token`` returns.
    """

    sub: str                          # user_id as string
    role: str = "viewer"
    exp: Optional[datetime] = None    # expiration time
    iat: Optional[datetime] = None    # issued-at time
    jti: Optional[str] = None         # unique token id


@dataclass(frozen=True)
class UserClaims:
    """Strongly-typed identity extracted from a validated token.

    This is the object injected by ``get_current_user()`` and checked
    by ``require_role()``.
    """

    user_id: UUID
    role: str = "viewer"

    # ---- convenience helpers ----------------------------------------
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_inspector(self) -> bool:
        return self.role in ("admin", "inspector")

    def has_role(self, *roles: str) -> bool:
        """Return ``True`` if the user's role is in *roles*."""
        return self.role in roles
