"""Authentication middleware for API Gateway.

Verifies JWT tokens and extracts user information from tokens.
Adds user context to request state for downstream use.

Features:
- JWT token verification using python-jose
- Skip authentication for public endpoints
- Extract user ID, email, and role from token
- Add user info to request state
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from ..config import settings

logger = logging.getLogger(__name__)

# Security scheme for JWT
security = HTTPBearer(auto_error=False)


# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = {
    "/health",
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
}

# Prefix-based public paths
PUBLIC_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi",
)


class AuthMiddleware:
    """Middleware for JWT authentication.

    Verifies JWT tokens on incoming requests and extracts user information.
    Skips authentication for public endpoints.
    """

    def __init__(self, app):
        """Initialize the middleware.

        Parameters
        ----------
        app:
            The FastAPI application
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        """Process the request through authentication middleware.

        Parameters
        ----------
        scope:
            ASGI scope
        receive:
            ASGI receive callable
        send:
            ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        path = request.url.path

        # Skip auth for public endpoints
        if self._is_public_endpoint(path):
            await self.app(scope, receive, send)
            return

        # Extract and verify token
        try:
            credentials = await self._extract_credentials(request)
            if credentials:
                payload = self._verify_token(credentials.credentials)
                # Add user info to request state
                request.state.user = self._extract_user_info(payload)
                request.state.authenticated = True
            else:
                request.state.user = None
                request.state.authenticated = False
        except HTTPException as exc:
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no auth required).

        Parameters
        ----------
        path:
            Request path

        Returns
        -------
        bool
            True if endpoint is public
        """
        if path in PUBLIC_ENDPOINTS:
            return True

        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True

        return False

    async def _extract_credentials(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        """Extract JWT token from request.

        Parameters
        ----------
        request:
            FastAPI request

        Returns
        -------
        HTTPAuthorizationCredentials or None
            Credentials if present
        """
        return await security(request)

    def _verify_token(self, token: str) -> dict:
        """Verify and decode JWT token.

        Parameters
        ----------
        token:
            JWT token string

        Returns
        -------
        dict
            Decoded token payload

        Raises
        ------
        HTTPException
            If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.JWT_AUDIENCE,
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _extract_user_info(self, payload: dict) -> dict:
        """Extract user information from token payload.

        Parameters
        ----------
        payload:
            Decoded JWT payload

        Returns
        -------
        dict
            User information dict
        """
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "PUBLIC"),
            "full_name": payload.get("full_name"),
        }


# =============================================================================
# Dependency functions for route handlers
# =============================================================================


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Get current user from request state or token.

    This is a dependency that can be used in route handlers.

    Parameters
    ----------
    request:
        FastAPI request
    credentials:
        Optional JWT credentials

    Returns
    -------
    dict or None
        User info dict or None if not authenticated
    """
    # Check if already set by middleware
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user

    # Try to extract from token
    if not credentials:
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
        )
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "PUBLIC"),
        }
    except JWTError:
        return None


async def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Require authentication for endpoint.

    Raises HTTPException if not authenticated.

    Parameters
    ----------
    request:
        FastAPI request
    credentials:
        JWT credentials

    Returns
    -------
    dict
        User info dict

    Raises
    ------
    HTTPException
        If not authenticated
    """
    user = await get_current_user(request, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_role(required_role: str):
    """Require specific role for endpoint.

    Creates a dependency that checks user role.

    Parameters
    ----------
    required_role:
        Required role name

    Returns
    -------
    Callable
        Dependency function
    """
    role_hierarchy = {
        "PUBLIC": 1,
        "FACTORY_OWNER": 2,
        "INSPECTOR": 3,
        "CITY_MANAGER": 4,
        "ADMIN": 5,
    }

    async def check_role(
        request: Request,
        user: dict = Depends(require_auth),
    ) -> dict:
        user_role = user.get("role", "PUBLIC")
        user_level = role_hierarchy.get(user_role, 1)
        required_level = role_hierarchy.get(required_role, 1)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role}",
            )
        return user

    return check_role


# Import Depends for the dependency functions
from fastapi import Depends
