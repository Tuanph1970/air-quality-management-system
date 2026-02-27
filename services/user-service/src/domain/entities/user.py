"""User entity for authentication and authorization.

The User entity is the core aggregate root of the user bounded context.
It manages user identity, credentials, and role-based access control.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from ..value_objects.email import Email
from ..value_objects.role import Role
from ..events.user_events import UserRegistered, UserPasswordChanged


@dataclass
class User:
    """User Entity - aggregate root for user management.

    Identity is defined by ``id`` (UUID). The email serves as a unique
    business identifier for authentication.

    Attributes
    ----------
    id:
        Unique user identifier (UUID)
    email:
        User's email address (Email value object)
    password_hash:
        Bcrypt hash of the user's password
    full_name:
        User's full name for display
    role:
        User's system role for authorization
    organization:
        Organization name (optional, for factory owners/inspectors)
    is_active:
        Whether the user account is active
    created_at:
        Account creation timestamp
    updated_at:
        Last update timestamp
    last_login_at:
        Last successful login timestamp
    """

    id: UUID
    email: Email
    password_hash: str
    full_name: str
    role: Role
    organization: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None

    _events: List = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------
    # Factory method (named-constructor pattern)
    # ------------------------------------------------------------------
    @classmethod
    def register(
        cls,
        email: str,
        password_hash: str,
        full_name: str,
        role: Role = Role.PUBLIC,
        organization: Optional[str] = None,
    ) -> User:
        """Register a new user.

        Factory method that creates a new user and emits a
        ``UserRegistered`` domain event.

        Parameters
        ----------
        email:
            User's email address
        password_hash:
            Pre-hashed password (use AuthService.hash_password)
        full_name:
            User's full name
        role:
            User's role (default: PUBLIC)
        organization:
            Organization name (optional)

        Returns
        -------
        User
            New User entity

        Raises
        ------
        ValueError
            If email format is invalid or password hash is empty
        """
        if not email:
            raise ValueError("Email is required")
        if not password_hash:
            raise ValueError("Password hash is required")

        email_obj = Email(email)
        user = cls(
            id=uuid4(),
            email=email_obj,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            organization=organization,
        )

        user._events.append(
            UserRegistered(
                user_id=user.id,
                email=str(email_obj),
                role=role.value,
            )
        )

        return user

    # ------------------------------------------------------------------
    # Authentication methods
    # ------------------------------------------------------------------
    def verify_password(self, password: str, verify_func) -> bool:
        """Verify a password against the stored hash.

        Parameters
        ----------
        password:
            Plain text password to verify
        verify_func:
            Function to verify password (e.g., bcrypt.verify)

        Returns
        -------
        bool
            True if password matches
        """
        return verify_func(password, self.password_hash)

    def change_password(self, new_password_hash: str) -> None:
        """Change the user's password.

        Updates the password hash and emits a ``UserPasswordChanged``
        domain event.

        Parameters
        ----------
        new_password_hash:
            New hashed password

        Raises
        ------
        ValueError
            If new password hash is empty
        """
        if not new_password_hash:
            raise ValueError("Password hash cannot be empty")

        self.password_hash = new_password_hash
        self.updated_at = datetime.now(timezone.utc)

        self._events.append(
            UserPasswordChanged(
                user_id=self.id,
                changed_at=self.updated_at,
            )
        )

    def record_login(self) -> None:
        """Record a successful login.

        Updates the last_login_at timestamp.
        """
        self.last_login_at = datetime.now(timezone.utc)
        self.updated_at = self.last_login_at

    # ------------------------------------------------------------------
    # Authorization methods
    # ------------------------------------------------------------------
    def has_role(self, role: Role) -> bool:
        """Check if user has a specific role.

        Parameters
        ----------
        role:
            Role to check

        Returns
        -------
        bool
            True if user has the role
        """
        return self.role == role

    def has_minimum_role(self, minimum_role: Role) -> bool:
        """Check if user has at least the minimum required role.

        Parameters
        ----------
        minimum_role:
            Minimum role required

        Returns
        -------
        bool
            True if user's role is equal or higher
        """
        return self.role.has_higher_or_equal_role(minimum_role)

    def can_access_resource(self, required_role: Role) -> bool:
        """Check if user can access a resource requiring a specific role.

        Parameters
        ----------
        required_role:
            Minimum role required for access

        Returns
        -------
        bool
            True if user has sufficient permissions
        """
        if not self.is_active:
            return False
        return self.has_minimum_role(required_role)

    # ------------------------------------------------------------------
    # State mutations
    # ------------------------------------------------------------------
    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def update_profile(
        self,
        full_name: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> None:
        """Update user profile information.

        Parameters
        ----------
        full_name:
            New full name (if provided)
        organization:
            New organization (if provided)
        """
        if full_name is not None:
            self.full_name = full_name
        if organization is not None:
            self.organization = organization
        self.updated_at = datetime.now(timezone.utc)

    def update_role(self, new_role: Role) -> None:
        """Update the user's role.

        Parameters
        ----------
        new_role:
            New role to assign
        """
        if self.role != new_role:
            old_role = self.role
            self.role = new_role
            self.updated_at = datetime.now(timezone.utc)
            # Could emit UserRoleChanged event here if needed

    # ------------------------------------------------------------------
    # Event collection
    # ------------------------------------------------------------------
    def collect_events(self) -> List:
        """Collect and clear pending domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    @property
    def is_admin(self) -> bool:
        """Check if user is an administrator."""
        return self.role == Role.ADMIN

    @property
    def email_str(self) -> str:
        """Get email as string."""
        return str(self.email)

    def to_dict(self) -> dict:
        """Convert user to dictionary (for serialization)."""
        return {
            "id": str(self.id),
            "email": str(self.email),
            "full_name": self.full_name,
            "role": self.role.value,
            "organization": self.organization,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
