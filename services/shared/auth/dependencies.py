"""FastAPI dependencies for authentication and role-based authorization.

Usage in any service's route file::

    from shared.auth.dependencies import get_current_user, require_role
    from shared.auth.models import UserClaims

    @router.get("/factories")
    async def list_factories(user: UserClaims = Depends(get_current_user)):
        ...

    @router.post("/factories/{id}/suspend")
    async def suspend(
        id: UUID,
        user: UserClaims = Depends(require_role(["admin", "inspector"])),
    ):
        ...
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .exceptions import AuthenticationError, AuthorizationError, AuthError
from .jwt_handler import verify_token
from .models import UserClaims

# ---------------------------------------------------------------------------
# Bearer-token extraction scheme
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Core dependency: authenticate
# ---------------------------------------------------------------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> UserClaims:
    """FastAPI dependency that extracts and validates a JWT.

    Reads the ``Authorization: Bearer <token>`` header, verifies the
    JWT signature and expiration, and returns a ``UserClaims`` instance.

    Raises ``HTTPException(401)`` on any authentication failure.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return verify_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ---------------------------------------------------------------------------
# Role-based dependency factory
# ---------------------------------------------------------------------------
def require_role(roles: List[str]):
    """Return a FastAPI dependency that enforces role membership.

    Parameters
    ----------
    roles:
        Allowed role names.  The dependency resolves to ``UserClaims``
        if the token's role is in the list, otherwise raises
        ``HTTPException(403)``.

    Example::

        @router.delete("/users/{id}")
        async def delete_user(
            id: UUID,
            user: UserClaims = Depends(require_role(["admin"])),
        ):
            ...
    """

    async def _role_checker(
        user: UserClaims = Depends(get_current_user),
    ) -> UserClaims:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not in {roles}",
            )
        return user

    return _role_checker


# ---------------------------------------------------------------------------
# Convenience: optional auth (for public-but-enriched endpoints)
# ---------------------------------------------------------------------------
async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> UserClaims | None:
    """Like ``get_current_user`` but returns ``None`` instead of 401.

    Useful for endpoints that work for anonymous users but provide
    richer responses to authenticated ones.
    """
    if credentials is None:
        return None

    try:
        return verify_token(credentials.credentials)
    except AuthError:
        return None
