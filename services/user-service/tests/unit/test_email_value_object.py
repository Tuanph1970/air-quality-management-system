"""Unit tests for Email value object."""
import pytest

from src.domain.value_objects.email import Email


class TestEmailCreation:
    """Tests for Email value object creation."""

    def test_create_valid_email(self):
        """Test creating email with valid format."""
        email = Email("test@example.com")
        assert email.value == "test@example.com"

    def test_email_normalized_to_lowercase(self):
        """Test email is normalized to lowercase."""
        email = Email("Test@Example.COM")
        assert email.value == "test@example.com"

    def test_email_stripped_whitespace(self):
        """Test email whitespace is stripped."""
        email = Email("  test@example.com  ")
        assert email.value == "test@example.com"

    def test_create_email_subdomain(self):
        """Test email with subdomain."""
        email = Email("user@mail.example.com")
        assert email.value == "user@mail.example.com"

    def test_create_email_plus_addressing(self):
        """Test email with plus addressing."""
        email = Email("user+tag@example.com")
        assert email.value == "user+tag@example.com"


class TestEmailValidation:
    """Tests for Email validation."""

    def test_invalid_email_no_at(self):
        """Test email without @ symbol."""
        with pytest.raises(ValueError, match="Invalid email"):
            Email("invalid.email.com")

    def test_invalid_email_no_domain(self):
        """Test email without domain."""
        with pytest.raises(ValueError, match="Invalid email"):
            Email("user@")

    def test_invalid_email_no_tld(self):
        """Test email without TLD."""
        with pytest.raises(ValueError, match="Invalid email"):
            Email("user@domain")

    def test_invalid_email_empty(self):
        """Test empty email."""
        with pytest.raises(ValueError, match="Invalid email"):
            Email("")

    def test_invalid_email_spaces(self):
        """Test email with spaces in local part."""
        with pytest.raises(ValueError, match="Invalid email"):
            Email("us er@example.com")


class TestEmailMethods:
    """Tests for Email value object methods."""

    def test_get_domain(self):
        """Test extracting domain from email."""
        email = Email("user@example.com")
        assert email.get_domain() == "example.com"

    def test_get_local_part(self):
        """Test extracting local part from email."""
        email = Email("user@example.com")
        assert email.get_local_part() == "user"

    def test_str_representation(self):
        """Test string representation."""
        email = Email("test@example.com")
        assert str(email) == "test@example.com"

    def test_equality_same_email(self):
        """Test equality with same email."""
        email1 = Email("test@example.com")
        email2 = Email("test@example.com")
        assert email1 == email2

    def test_equality_different_case(self):
        """Test equality ignores case."""
        email1 = Email("Test@Example.COM")
        email2 = Email("test@example.com")
        assert email1 == email2

    def test_equality_with_string(self):
        """Test equality with string."""
        email = Email("test@example.com")
        assert email == "test@example.com"
        assert email == "TEST@EXAMPLE.COM"

    def test_hash_consistency(self):
        """Test hash is consistent."""
        email1 = Email("test@example.com")
        email2 = Email("test@example.com")
        assert hash(email1) == hash(email2)

    def test_hash_usable_in_set(self):
        """Test email can be used in set."""
        email1 = Email("test@example.com")
        email2 = Email("test@example.com")
        email3 = Email("other@example.com")
        
        emails = {email1, email2, email3}
        assert len(emails) == 2  # email1 and email2 are duplicates
