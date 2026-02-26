"""Authentication domain service."""
from abc import ABC, abstractmethod
from typing import Optional


class AuthService(ABC):
    """Abstract authentication service."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, plain: str, hashed: str) -> bool:
        pass

    @abstractmethod
    def create_token(self, data: dict) -> str:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Optional[dict]:
        pass
