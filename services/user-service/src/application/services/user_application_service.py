"""User application service.

Orchestrates user-related use cases:
- Register new user
- Login (authenticate and issue token)
- Get user by ID
- Refresh token

**Application layer**: Coordinates between domain services, repositories,
and infrastructure. Contains no business rules.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from ...config import settings
from ...domain.entities.user import User
from ...domain.exceptions.user_exceptions import (
    InsufficientPermissionsError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserNotFoundError,
)
from ...domain.repositories.user_repository import UserRepository
from ...domain.services.auth_service import AuthService
from ...domain.value_objects.role import Role
from ..commands.login_command import LoginCommand
from ..commands.register_user_command import RegisterUserCommand
from ..dto.user_dto import TokenResponse, UserDTO

logger = logging.getLogger(__name__)


class UserApplicationService:
    """Application service for user operations.

    Coordinates between:
    - User entity (domain)
    - AuthService (domain service)
    - UserRepository (infrastructure)
    - JWT utilities (infrastructure)
    """

    def __init__(
        self,
        user_repository: UserRepository,
        auth_service: AuthService,
        jwt_handler: Optional[Any] = None,
    ):
        """Initialize the application service.

        Parameters
        ----------
        user_repository:
            Repository for user persistence
        auth_service:
            Domain service for password operations
        jwt_handler:
            JWT handler for token operations (optional)
        """
        self.user_repository = user_repository
        self.auth_service = auth_service
        self.jwt_handler = jwt_handler

    # ------------------------------------------------------------------
    # Use Case: Register new user
    # ------------------------------------------------------------------
    async def register(self, command: RegisterUserCommand) -> UserDTO:
        """Register a new user.

        Flow:
        1. Check if email already exists
        2. Validate password strength
        3. Hash password
        4. Create user entity
        5. Save to repository
        6. Return user DTO

        Parameters
        ----------
        command:
            Registration command with user data

        Returns
        -------
        UserDTO
            Created user data

        Raises
        ------
        UserAlreadyExistsError
            If email is already registered
        PasswordTooWeakError
            If password doesn't meet requirements
        """
        # Check if email exists
        email_lower = command.email.lower().strip()
        exists = await self.user_repository.exists_by_email(email_lower)
        if exists:
            raise UserAlreadyExistsError(email_lower)

        # Validate password strength
        is_valid, error_msg = AuthService.validate_password_strength(command.password)
        if not is_valid:
            from ...domain.exceptions.user_exceptions import PasswordTooWeakError
            raise PasswordTooWeakError(error_msg)

        # Hash password
        password_hash = self.auth_service.hash_password(command.password)

        # Map role string to Role enum
        try:
            role = Role(command.role.upper())
        except ValueError:
            role = Role.PUBLIC

        # Create user entity
        user = User.register(
            email=email_lower,
            password_hash=password_hash,
            full_name=command.full_name,
            role=role,
            organization=command.organization,
        )

        # Save to repository
        saved_user = await self.user_repository.save(user)

        logger.info("User registered: id=%s email=%s", saved_user.id, email_lower)
        return UserDTO.from_entity(saved_user)

    # ------------------------------------------------------------------
    # Use Case: Login (authenticate user)
    # ------------------------------------------------------------------
    async def login(self, command: LoginCommand) -> TokenResponse:
        """Authenticate user and issue JWT token.

        Flow:
        1. Find user by email
        2. Verify password
        3. Check user is active
        4. Record login
        5. Generate JWT token
        6. Return token response

        Parameters
        ----------
        command:
            Login command with credentials

        Returns
        -------
        TokenResponse
            JWT token and user info

        Raises
        ------
        InvalidCredentialsError
            If credentials are invalid
        UserInactiveError
            If user account is inactive
        """
        email_lower = command.email.lower().strip()

        # Find user by email
        user = await self.user_repository.get_by_email(email_lower)
        if not user:
            # Don't reveal if email exists
            raise InvalidCredentialsError()

        # Check if user is active
        if not user.is_active:
            raise UserInactiveError(email_lower)

        # Verify password
        if not user.verify_password(command.password, self.auth_service.verify_password):
            raise InvalidCredentialsError()

        # Record login
        user.record_login()
        await self.user_repository.save(user)

        # Generate JWT token
        access_token = self._generate_access_token(user)

        logger.info("User logged in: id=%s email=%s", user.id, email_lower)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
            user=UserDTO.from_entity(user),
        )

    # ------------------------------------------------------------------
    # Use Case: Get user by ID
    # ------------------------------------------------------------------
    async def get_user(self, user_id: str) -> UserDTO:
        """Get user by ID.

        Parameters
        ----------
        user_id:
            User ID (UUID string)

        Returns
        -------
        UserDTO
            User data

        Raises
        ------
        UserNotFoundError
            If user doesn't exist
        """
        from uuid import UUID

        try:
            uuid_id = UUID(user_id)
        except ValueError:
            raise UserNotFoundError(user_id)

        user = await self.user_repository.get_by_id(uuid_id)
        if not user:
            raise UserNotFoundError(user_id)

        return UserDTO.from_entity(user)

    # ------------------------------------------------------------------
    # Use Case: Get current user from token
    # ------------------------------------------------------------------
    async def get_current_user(self, token: str) -> UserDTO:
        """Get current user from JWT token.

        Parameters
        ----------
        token:
            JWT access token

        Returns
        -------
        UserDTO
            Current user data

        Raises
        ------
        InvalidCredentialsError
            If token is invalid
        UserNotFoundError
            If user doesn't exist
        """
        if not self.jwt_handler:
            raise InvalidCredentialsError()

        # Decode token
        payload = self.jwt_handler.decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise InvalidCredentialsError()

        return await self.get_user(user_id)

    # ------------------------------------------------------------------
    # Use Case: Refresh token
    # ------------------------------------------------------------------
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token.

        Parameters
        ----------
        refresh_token:
            Refresh token

        Returns
        -------
        TokenResponse
            New access token

        Raises
        ------
        InvalidCredentialsError
            If refresh token is invalid
        """
        if not self.jwt_handler:
            raise InvalidCredentialsError()

        # Decode refresh token
        payload = self.jwt_handler.decode_refresh_token(refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            raise InvalidCredentialsError()

        # Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidCredentialsError()

        # Generate new access token
        access_token = self._generate_access_token(user)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # Use Case: Update user profile
    # ------------------------------------------------------------------
    async def update_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> UserDTO:
        """Update user profile.

        Parameters
        ----------
        user_id:
            User ID
        full_name:
            New full name
        organization:
            New organization

        Returns
        -------
        UserDTO
            Updated user data
        """
        from uuid import UUID

        uuid_id = UUID(user_id)
        user = await self.user_repository.get_by_id(uuid_id)
        if not user:
            raise UserNotFoundError(user_id)

        user.update_profile(full_name=full_name, organization=organization)
        saved = await self.user_repository.save(user)

        return UserDTO.from_entity(saved)

    # ------------------------------------------------------------------
    # Use Case: Change password
    # ------------------------------------------------------------------
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> UserDTO:
        """Change user password.

        Parameters
        ----------
        user_id:
            User ID
        current_password:
            Current password for verification
        new_password:
            New password

        Returns
        -------
        UserDTO
            Updated user data

        Raises
        ------
        InvalidCredentialsError
            If current password is wrong
        PasswordTooWeakError
            If new password is too weak
        """
        from uuid import UUID
        from ...domain.exceptions.user_exceptions import PasswordTooWeakError

        uuid_id = UUID(user_id)
        user = await self.user_repository.get_by_id(uuid_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Verify current password
        if not user.verify_password(current_password, self.auth_service.verify_password):
            raise InvalidCredentialsError()

        # Validate new password
        is_valid, error_msg = AuthService.validate_password_strength(new_password)
        if not is_valid:
            raise PasswordTooWeakError(error_msg)

        # Hash and update password
        new_hash = self.auth_service.hash_password(new_password)
        user.change_password(new_hash)
        saved = await self.user_repository.save(user)

        return UserDTO.from_entity(saved)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _generate_access_token(self, user: User) -> str:
        """Generate JWT access token for a user.

        Parameters
        ----------
        user:
            User entity

        Returns
        -------
        str
            JWT access token
        """
        if not self.jwt_handler:
            # Fallback: use shared JWT handler directly
            from shared.auth.jwt_handler import create_access_token

            return create_access_token(
                user_id=str(user.id),
                email=str(user.email),
                role=user.role.value,
                expires_delta=timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
            )

        return self.jwt_handler.create_access_token(
            user_id=str(user.id),
            email=str(user.email),
            role=user.role.value,
        )


# =============================================================================
# Dependency Injection for FastAPI
# =============================================================================


def get_user_application_service():
    """FastAPI dependency that yields a UserApplicationService instance.

    Usage::

        @router.post("/auth/login")
        async def login(
            command: LoginCommand,
            service: UserApplicationService = Depends(get_user_application_service)
        ):
            ...
    """
    from ...infrastructure.persistence.database import get_session_maker
    from ...infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository

    async def _generate():
        async with get_session_maker()() as session:
            user_repo = SQLAlchemyUserRepository(session)
            auth_service = AuthService()

            service = UserApplicationService(
                user_repository=user_repo,
                auth_service=auth_service,
            )
            try:
                yield service
            finally:
                pass

    return _generate()
