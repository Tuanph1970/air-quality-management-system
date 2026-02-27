"""Authentication domain service.

Provides password hashing and verification using bcrypt.
This is a pure domain service with no infrastructure dependencies.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

import bcrypt


class AuthService:
    """Authentication domain service for password operations.

    Provides secure password hashing and verification using bcrypt.
    The work factor (cost) is configurable for security vs performance.
    """

    DEFAULT_ROUNDS = 12  # Bcrypt cost factor

    @staticmethod
    def hash_password(password: str, rounds: int = None) -> str:
        """Hash a password using bcrypt.

        Parameters
        ----------
        password:
            Plain text password to hash
        rounds:
            Bcrypt cost factor (default: 12)
            Higher = more secure but slower

        Returns
        -------
        str
            Bcrypt hash string (includes salt and rounds)

        Raises
        ------
        ValueError
            If password is empty or too short
        """
        if not password:
            raise ValueError("Password cannot be empty")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        rounds = rounds or AuthService.DEFAULT_ROUNDS

        # Encode password to bytes
        password_bytes = password.encode("utf-8")

        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)

        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against a bcrypt hash.

        Parameters
        ----------
        password:
            Plain text password to verify
        password_hash:
            Bcrypt hash to verify against

        Returns
        -------
        bool
            True if password matches the hash

        Raises
        ------
        ValueError
            If password or hash is empty
        """
        if not password:
            raise ValueError("Password cannot be empty")
        if not password_hash:
            raise ValueError("Password hash cannot be empty")

        # Encode to bytes
        password_bytes = password.encode("utf-8")
        hash_bytes = password_hash.encode("utf-8")

        # Verify
        return bcrypt.checkpw(password_bytes, hash_bytes)

    @staticmethod
    def needs_rehash(password_hash: str, new_rounds: int = None) -> bool:
        """Check if a password hash needs to be rehashed with new rounds.

        As hardware improves, we can increase the bcrypt rounds to maintain
        security. This method checks if a hash should be upgraded.

        Parameters
        ----------
        password_hash:
            Existing bcrypt hash
        new_rounds:
            Target rounds (default: DEFAULT_ROUNDS)

        Returns
        -------
        bool
            True if hash should be rehashed
        """
        new_rounds = new_rounds or AuthService.DEFAULT_ROUNDS

        try:
            # Extract rounds from existing hash
            # Format: $2b$XX$... where XX is the rounds
            parts = password_hash.split("$")
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds < new_rounds
        except (ValueError, IndexError):
            # If we can't parse the hash, assume it needs rehashing
            return True

        return False

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password meets security requirements.

        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Parameters
        ----------
        password:
            Password to validate

        Returns
        -------
        tuple[bool, str]
            (is_valid, error_message)
            error_message is empty if valid
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"

        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character"

        return True, ""
