"""Email value object for user authentication.

Encapsulates email validation and normalization.
Ensures all emails in the system are valid and consistently formatted.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """Value Object for email addresses.

    Immutable value object that validates email format on creation.
    Comparison is based on the normalized email string.

    Attributes
    ----------
    value:
        The email address string (lowercase, stripped)
    """

    value: str

    def __post_init__(self) -> None:
        """Validate email format after initialization."""
        # First normalize: strip whitespace and lowercase
        normalized = self.value.lower().strip()
        
        if not self._is_valid_email(normalized):
            raise ValueError(f"Invalid email format: {self.value}")

        # Normalize: lowercase and strip whitespace
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format using regex.

        Pattern checks for:
        - Local part: alphanumeric, dots, underscores, percent, plus, hyphens
        - @ symbol
        - Domain: alphanumeric, dots, hyphens
        - TLD: at least 2 characters

        Parameters
        ----------
        email:
            Email string to validate

        Returns
        -------
        bool
            True if valid email format
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def __str__(self) -> str:
        """Return string representation."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """Check equality with another Email or string."""
        if isinstance(other, Email):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.lower().strip()
        return False

    def __hash__(self) -> int:
        """Return hash based on email value."""
        return hash(self.value)

    @classmethod
    def create(cls, email: str) -> Email:
        """Factory method to create an Email value object.

        Parameters
        ----------
        email:
            Email address string

        Returns
        -------
        Email
            New Email value object

        Raises
        ------
        ValueError
            If email format is invalid
        """
        return cls(email)

    def get_domain(self) -> str:
        """Extract domain from email.

        Returns
        -------
        str
            Domain part of the email (after @)
        """
        return self.value.split("@")[1]

    def get_local_part(self) -> str:
        """Extract local part from email.

        Returns
        -------
        str
            Local part of the email (before @)
        """
        return self.value.split("@")[0]
