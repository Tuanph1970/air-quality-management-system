"""Shared JWT authentication library for all AQMS services."""

from .exceptions import (
    AuthError,
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    TokenExpiredError,
)
from .jwt_handler import (
    JWT_ALGORITHM,
    JWT_SECRET,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_token,
    verify_token,
)
from .models import TokenPayload, UserClaims
from .dependencies import get_current_user, get_optional_user, require_role

__all__ = [
    # Exceptions
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "InvalidTokenError",
    "TokenExpiredError",
    # JWT functions
    "create_access_token",
    "verify_token",
    "decode_token",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    # Models
    "TokenPayload",
    "UserClaims",
    # FastAPI dependencies
    "get_current_user",
    "get_optional_user",
    "require_role",
]
