"""Login command."""
from dataclasses import dataclass


@dataclass
class LoginCommand:
    """Data required for user login.

    Attributes
    ----------
    email:
        User's email address
    password:
        Plain text password
    """

    email: str
    password: str
