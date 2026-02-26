"""Command to authenticate a user."""
from dataclasses import dataclass


@dataclass
class LoginCommand:
    email: str
    password: str
