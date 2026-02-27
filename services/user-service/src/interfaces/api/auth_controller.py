"""Authentication API Controller.

REST API endpoints for:
- User registration
- User login
- Token refresh
- Get current user
- Profile management
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...application.services.user_application_service import (
    UserApplicationService,
    get_user_application_service,
)
from .schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["authentication"])

# Security scheme for JWT
security = HTTPBearer(auto_error=False)


# =============================================================================
# Dependency Injection
# =============================================================================


def get_service() -> UserApplicationService:
    """Inject the user application service."""
    return next(get_user_application_service())


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    service: UserApplicationService = Depends(get_service),
) -> str:
    """Extract and validate user ID from JWT token.

    Parameters
    ----------
    credentials:
        HTTP Authorization header with Bearer token
    service:
        User application service

    Returns
    -------
    str
        User ID from token

    Raises
    ------
    HTTPException
        If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_dto = await service.get_current_user(credentials.credentials)
        return str(user_dto.id)
    except Exception as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# Authentication Endpoints
# =============================================================================


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    service: UserApplicationService = Depends(get_service),
) -> UserResponse:
    """Register a new user.

    Creates a new user account with the provided credentials.
    The user is assigned the PUBLIC role by default.

    - **email**: User's email address (must be unique)
    - **password**: Password (min 8 chars, must include uppercase, lowercase, digit, special char)
    - **full_name**: User's full name
    - **role**: Optional role (PUBLIC, FACTORY_OWNER, INSPECTOR, CITY_MANAGER, ADMIN)
    - **organization**: Optional organization name
    """
    from ...application.commands.register_user_command import RegisterUserCommand

    command = RegisterUserCommand(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role=request.role,
        organization=request.organization,
    )

    try:
        user_dto = await service.register(command)
        return UserResponse(
            id=str(user_dto.id),
            email=user_dto.email,
            full_name=user_dto.full_name,
            role=user_dto.role,
            organization=user_dto.organization,
            is_active=user_dto.is_active,
            created_at=user_dto.created_at,
            last_login_at=user_dto.last_login_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    service: UserApplicationService = Depends(get_service),
) -> TokenResponse:
    """Authenticate user and issue JWT token.

    Validates credentials and returns a JWT access token.
    The token is valid for 1 hour by default.

    - **email**: User's email address
    - **password**: User's password
    """
    from ...application.commands.login_command import LoginCommand

    command = LoginCommand(
        email=request.email,
        password=request.password,
    )

    try:
        token_response = await service.login(command)
        return TokenResponse(
            access_token=token_response.access_token,
            token_type=token_response.token_type,
            expires_in=token_response.expires_in,
            user=UserResponse(
                id=str(token_response.user.id),
                email=token_response.user.email,
                full_name=token_response.user.full_name,
                role=token_response.user.role,
                organization=token_response.user.organization,
                is_active=token_response.user.is_active,
                created_at=token_response.user.created_at,
                last_login_at=token_response.user.last_login_at,
            ) if token_response.user else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    service: UserApplicationService = Depends(get_service),
) -> TokenResponse:
    """Refresh access token using refresh token.

    Exchange a valid refresh token for a new access token.
    """
    try:
        token_response = await service.refresh_token(request.refresh_token)
        return TokenResponse(
            access_token=token_response.access_token,
            token_type=token_response.token_type,
            expires_in=token_response.expires_in,
        )
    except Exception as e:
        logger.warning(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# User Management Endpoints
# =============================================================================


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user(
    service: UserApplicationService = Depends(get_service),
    user_id: str = Depends(get_current_user_id),
) -> UserResponse:
    """Get current authenticated user.

    Requires valid JWT token in Authorization header.
    """
    user_dto = await service.get_user(user_id)
    return UserResponse(
        id=str(user_dto.id),
        email=user_dto.email,
        full_name=user_dto.full_name,
        role=user_dto.role,
        organization=user_dto.organization,
        is_active=user_dto.is_active,
        created_at=user_dto.created_at,
        last_login_at=user_dto.last_login_at,
    )


@router.put("/auth/profile", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    service: UserApplicationService = Depends(get_service),
    user_id: str = Depends(get_current_user_id),
) -> UserResponse:
    """Update user profile.

    Requires valid JWT token. Users can update their own profile.
    """
    user_dto = await service.update_profile(
        user_id=user_id,
        full_name=request.full_name,
        organization=request.organization,
    )
    return UserResponse(
        id=str(user_dto.id),
        email=user_dto.email,
        full_name=user_dto.full_name,
        role=user_dto.role,
        organization=user_dto.organization,
        is_active=user_dto.is_active,
        created_at=user_dto.created_at,
        last_login_at=user_dto.last_login_at,
    )


@router.post("/auth/change-password", response_model=UserResponse)
async def change_password(
    request: ChangePasswordRequest,
    service: UserApplicationService = Depends(get_service),
    user_id: str = Depends(get_current_user_id),
) -> UserResponse:
    """Change user password.

    Requires valid JWT token. User must provide current password.
    """
    user_dto = await service.change_password(
        user_id=user_id,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    return UserResponse(
        id=str(user_dto.id),
        email=user_dto.email,
        full_name=user_dto.full_name,
        role=user_dto.role,
        organization=user_dto.organization,
        is_active=user_dto.is_active,
        created_at=user_dto.created_at,
        last_login_at=user_dto.last_login_at,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    service: UserApplicationService = Depends(get_service),
    current_user_id: str = Depends(get_current_user_id),
) -> UserResponse:
    """Get user by ID.

    Requires valid JWT token. Users can only view their own profile
    unless they have ADMIN role.
    """
    # Check permission (simplified - in production, check roles properly)
    if user_id != current_user_id:
        requesting_user = await service.get_user(current_user_id)
        if requesting_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view other users",
            )

    user_dto = await service.get_user(user_id)
    return UserResponse(
        id=str(user_dto.id),
        email=user_dto.email,
        full_name=user_dto.full_name,
        role=user_dto.role,
        organization=user_dto.organization,
        is_active=user_dto.is_active,
        created_at=user_dto.created_at,
        last_login_at=user_dto.last_login_at,
    )
