"""Role value object for user authorization.

Defines the system roles and their permissions hierarchy.
Roles follow a hierarchical structure for access control.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """User role enumeration with permission hierarchy.

    Role hierarchy (highest to lowest):
    - ADMIN: Full system access, user management
    - CITY_MANAGER: City-wide oversight, report access
    - INSPECTOR: Factory inspection, violation management
    - FACTORY_OWNER: Factory management, compliance reporting
    - PUBLIC: Read-only access to public data

    Inherits from ``str`` for easy JSON serialization and database storage.
    """

    ADMIN = "ADMIN"
    CITY_MANAGER = "CITY_MANAGER"
    INSPECTOR = "INSPECTOR"
    FACTORY_OWNER = "FACTORY_OWNER"
    PUBLIC = "PUBLIC"

    # ------------------------------------------------------------------
    # Permission checks
    # ------------------------------------------------------------------
    @property
    def can_manage_users(self) -> bool:
        """Check if role can manage other users."""
        return self == Role.ADMIN

    @property
    def can_manage_factories(self) -> bool:
        """Check if role can manage factories."""
        return self in (Role.ADMIN, Role.INSPECTOR, Role.FACTORY_OWNER)

    @property
    def can_inspect_factories(self) -> bool:
        """Check if role can perform factory inspections."""
        return self in (Role.ADMIN, Role.INSPECTOR, Role.CITY_MANAGER)

    @property
    def can_view_violations(self) -> bool:
        """Check if role can view violations."""
        return self in (
            Role.ADMIN,
            Role.INSPECTOR,
            Role.CITY_MANAGER,
            Role.FACTORY_OWNER,
        )

    @property
    def can_resolve_violations(self) -> bool:
        """Check if role can resolve violations."""
        return self in (Role.ADMIN, Role.INSPECTOR, Role.CITY_MANAGER)

    @property
    def can_view_reports(self) -> bool:
        """Check if role can view system reports."""
        return self in (
            Role.ADMIN,
            Role.INSPECTOR,
            Role.CITY_MANAGER,
            Role.FACTORY_OWNER,
        )

    @property
    def can_view_all_data(self) -> bool:
        """Check if role can view all system data."""
        return self in (Role.ADMIN, Role.CITY_MANAGER)

    @property
    def is_admin(self) -> bool:
        """Check if role is ADMIN."""
        return self == Role.ADMIN

    @property
    def is_factory_related(self) -> bool:
        """Check if role is related to factory operations."""
        return self in (Role.FACTORY_OWNER, Role.INSPECTOR)

    # ------------------------------------------------------------------
    # Hierarchy comparison
    # ------------------------------------------------------------------
    @property
    def hierarchy_level(self) -> int:
        """Get numeric hierarchy level (higher = more permissions).

        Returns
        -------
        int
            Hierarchy level (5=ADMIN, 1=PUBLIC)
        """
        return _ROLE_HIERARCHY.get(self, 0)

    def has_higher_or_equal_role(self, other: "Role") -> bool:
        """Check if this role has higher or equal permissions.

        Parameters
        ----------
        other:
            Another Role to compare against

        Returns
        -------
        bool
            True if this role has equal or higher permissions
        """
        return self.hierarchy_level >= other.hierarchy_level

    def has_lower_role(self, other: "Role") -> bool:
        """Check if this role has lower permissions.

        Parameters
        ----------
        other:
            Another Role to compare against

        Returns
        -------
        bool
            True if this role has lower permissions
        """
        return self.hierarchy_level < other.hierarchy_level


# Role hierarchy mapping (higher number = more permissions)
_ROLE_HIERARCHY = {
    Role.ADMIN: 5,
    Role.CITY_MANAGER: 4,
    Role.INSPECTOR: 3,
    Role.FACTORY_OWNER: 2,
    Role.PUBLIC: 1,
}
