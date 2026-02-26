"""JWT creation, verification, and decoding.

Uses ``python-jose`` for all cryptographic operations.  Every service
imports these functions to either issue tokens (user-service) or
validate them (all other services via the ``get_current_user``
dependency).

Configuration is read from environment variables at import time with
safe defaults for local development.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from jose import JWTError, jwt

from .exceptions import InvalidTokenError, TokenExpiredError
from .models import TokenPayload, UserClaims

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-key")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"),
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def create_access_token(
    user_id: UUID,
    role: str = "viewer",
    *,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT containing the user's identity and role.

    Parameters
    ----------
    user_id:
        The user's unique identifier — stored in the ``sub`` claim.
    role:
        Role string (``admin``, ``inspector``, ``operator``, ``viewer``).
    expires_delta:
        Custom lifetime.  Defaults to ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns
    -------
    str
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expire,
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> UserClaims:
    """Validate a JWT and return strongly-typed ``UserClaims``.

    This is the primary entry point used by the ``get_current_user``
    FastAPI dependency.

    Raises
    ------
    TokenExpiredError
        If the token's ``exp`` claim is in the past.
    InvalidTokenError
        If the token is malformed, has an invalid signature, or is
        missing required claims.
    """
    payload = decode_token(token)

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Token missing 'sub' claim")

    try:
        user_id = UUID(sub)
    except ValueError:
        raise InvalidTokenError("Token 'sub' is not a valid UUID")

    role = payload.get("role", "viewer")
    return UserClaims(user_id=user_id, role=role)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT, returning the raw claims dict.

    Lower-level than ``verify_token`` — useful when a service needs
    access to all claims (``exp``, ``iat``, ``jti``, etc.).

    Raises
    ------
    TokenExpiredError
        If the token has expired.
    InvalidTokenError
        For any other decoding/validation failure.
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
        return payload
    except JWTError as exc:
        msg = str(exc).lower()
        if "expired" in msg:
            raise TokenExpiredError() from exc
        raise InvalidTokenError(str(exc)) from exc
