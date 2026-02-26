"""Password value object."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Password:
    """Value Object for passwords."""

    value: str

    def __post_init__(self):
        if len(self.value) < 8:
            raise ValueError("Password must be at least 8 characters")
