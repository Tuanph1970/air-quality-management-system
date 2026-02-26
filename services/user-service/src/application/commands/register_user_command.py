"""Command to register a new user."""
from dataclasses import dataclass


@dataclass
class RegisterUserCommand:
    email: str
    password: str
    full_name: str
    role: str = "viewer"
