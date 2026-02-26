"""Email value object."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """Value Object for email addresses."""

    value: str

    def __post_init__(self):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, self.value):
            raise ValueError(f"Invalid email: {self.value}")
