"""Unit tests for AuthService domain service."""
import pytest

from src.domain.services.auth_service import AuthService


class TestPasswordHashing:
    """Tests for password hashing."""

    def test_hash_password_returns_string(self):
        """Test hash_password returns a string."""
        result = AuthService.hash_password("SecurePass123!")
        assert isinstance(result, str)

    def test_hash_password_different_salts(self):
        """Test same password produces different hashes."""
        password = "SecurePass123!"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        
        assert hash1 != hash2  # Different salts

    def test_hash_password_starts_with_bcrypt_prefix(self):
        """Test hash has bcrypt prefix."""
        result = AuthService.hash_password("SecurePass123!")
        assert result.startswith("$2b$")

    def test_hash_password_empty_raises(self):
        """Test empty password raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            AuthService.hash_password("")

    def test_hash_password_short_raises(self):
        """Test short password raises ValueError."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            AuthService.hash_password("short")


class TestPasswordVerification:
    """Tests for password verification."""

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "SecurePass123!"
        password_hash = AuthService.hash_password(password)
        
        assert AuthService.verify_password(password, password_hash) is True

    def test_verify_wrong_password(self):
        """Test verifying wrong password."""
        password = "SecurePass123!"
        password_hash = AuthService.hash_password(password)
        
        assert AuthService.verify_password("WrongPass456!", password_hash) is False

    def test_verify_empty_password_raises(self):
        """Test empty password raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            AuthService.verify_password("", "some_hash")

    def test_verify_empty_hash_raises(self):
        """Test empty hash raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            AuthService.verify_password("password", "")


class TestNeedsRehash:
    """Tests for hash rehashing detection."""

    def test_needs_rehash_lower_rounds(self):
        """Test hash with lower rounds needs rehashing."""
        # Create hash with low rounds
        old_hash = AuthService.hash_password("SecurePass123!", rounds=4)
        
        assert AuthService.needs_rehash(old_hash, new_rounds=12) is True

    def test_needs_rehash_same_rounds(self):
        """Test hash with same rounds doesn't need rehashing."""
        password_hash = AuthService.hash_password("SecurePass123!", rounds=12)
        
        assert AuthService.needs_rehash(password_hash, new_rounds=12) is False


class TestPasswordStrength:
    """Tests for password strength validation."""

    def test_strong_password(self):
        """Test strong password passes validation."""
        is_valid, error = AuthService.validate_password_strength("SecurePass123!")
        assert is_valid is True
        assert error == ""

    def test_weak_password_too_short(self):
        """Test short password fails validation."""
        is_valid, error = AuthService.validate_password_strength("Short1!")
        assert is_valid is False
        assert "8 characters" in error

    def test_weak_password_no_uppercase(self):
        """Test password without uppercase fails."""
        is_valid, error = AuthService.validate_password_strength("lowercase123!")
        assert is_valid is False
        assert "uppercase" in error

    def test_weak_password_no_lowercase(self):
        """Test password without lowercase fails."""
        is_valid, error = AuthService.validate_password_strength("UPPERCASE123!")
        assert is_valid is False
        assert "lowercase" in error

    def test_weak_password_no_digit(self):
        """Test password without digit fails."""
        is_valid, error = AuthService.validate_password_strength("NoDigitsHere!")
        assert is_valid is False
        assert "digit" in error

    def test_weak_password_no_special(self):
        """Test password without special char fails."""
        is_valid, error = AuthService.validate_password_strength("NoSpecial123")
        assert is_valid is False
        assert "special character" in error
