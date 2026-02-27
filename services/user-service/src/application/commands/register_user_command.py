"""Register user command."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RegisterUserCommand:
    """Data required to register a new user.

    Attributes
    ----------
    email:
        User's email address
    password:
        Plain text password (will be hashed)
    full_name:
        User's full name
    role:
        User's role (default: PUBLIC)
    organization:
        Organization name (optional)
    """

    email: str
    password: str
    full_name: str
    role: str = "PUBLIC"
    organization: Optional[str] = None
