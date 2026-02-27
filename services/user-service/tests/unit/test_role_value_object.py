"""Unit tests for Role value object."""
import pytest

from src.domain.value_objects.role import Role


class TestRoleCreation:
    """Tests for Role enum."""

    def test_role_values(self):
        """Test all role values exist."""
        assert Role.ADMIN.value == "ADMIN"
        assert Role.CITY_MANAGER.value == "CITY_MANAGER"
        assert Role.INSPECTOR.value == "INSPECTOR"
        assert Role.FACTORY_OWNER.value == "FACTORY_OWNER"
        assert Role.PUBLIC.value == "PUBLIC"

    def test_role_string_comparison(self):
        """Test role can be compared to string."""
        assert Role.ADMIN == "ADMIN"
        assert "ADMIN" == Role.ADMIN


class TestRolePermissions:
    """Tests for Role permission properties."""

    def test_admin_permissions(self):
        """Test ADMIN role permissions."""
        assert Role.ADMIN.can_manage_users is True
        assert Role.ADMIN.can_manage_factories is True
        assert Role.ADMIN.can_inspect_factories is True
        assert Role.ADMIN.can_view_all_data is True
        assert Role.ADMIN.is_admin is True

    def test_city_manager_permissions(self):
        """Test CITY_MANAGER role permissions."""
        assert Role.CITY_MANAGER.can_manage_users is False
        assert Role.CITY_MANAGER.can_manage_factories is False
        assert Role.CITY_MANAGER.can_inspect_factories is True
        assert Role.CITY_MANAGER.can_view_all_data is True
        assert Role.CITY_MANAGER.is_admin is False

    def test_inspector_permissions(self):
        """Test INSPECTOR role permissions."""
        assert Role.INSPECTOR.can_manage_users is False
        assert Role.INSPECTOR.can_manage_factories is True
        assert Role.INSPECTOR.can_inspect_factories is True
        assert Role.INSPECTOR.can_view_violations is True
        assert Role.INSPECTOR.can_resolve_violations is True

    def test_factory_owner_permissions(self):
        """Test FACTORY_OWNER role permissions."""
        assert Role.FACTORY_OWNER.can_manage_users is False
        assert Role.FACTORY_OWNER.can_manage_factories is True
        assert Role.FACTORY_OWNER.can_inspect_factories is False
        assert Role.FACTORY_OWNER.can_view_violations is True
        assert Role.FACTORY_OWNER.can_resolve_violations is False

    def test_public_permissions(self):
        """Test PUBLIC role permissions."""
        assert Role.PUBLIC.can_manage_users is False
        assert Role.PUBLIC.can_manage_factories is False
        assert Role.PUBLIC.can_inspect_factories is False
        assert Role.PUBLIC.can_view_violations is False
        assert Role.PUBLIC.can_view_all_data is False


class TestRoleHierarchy:
    """Tests for Role hierarchy."""

    def test_hierarchy_levels(self):
        """Test role hierarchy levels."""
        assert Role.ADMIN.hierarchy_level == 5
        assert Role.CITY_MANAGER.hierarchy_level == 4
        assert Role.INSPECTOR.hierarchy_level == 3
        assert Role.FACTORY_OWNER.hierarchy_level == 2
        assert Role.PUBLIC.hierarchy_level == 1

    def test_has_higher_or_equal_role(self):
        """Test role comparison."""
        assert Role.ADMIN.has_higher_or_equal_role(Role.CITY_MANAGER) is True
        assert Role.CITY_MANAGER.has_higher_or_equal_role(Role.ADMIN) is False
        assert Role.INSPECTOR.has_higher_or_equal_role(Role.INSPECTOR) is True

    def test_has_lower_role(self):
        """Test lower role comparison."""
        assert Role.PUBLIC.has_lower_role(Role.ADMIN) is True
        assert Role.ADMIN.has_lower_role(Role.PUBLIC) is False
