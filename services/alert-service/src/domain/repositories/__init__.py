"""Alert domain repository interfaces."""
from .alert_config_repository import AlertConfigRepository
from .violation_repository import ViolationRepository

__all__ = ["AlertConfigRepository", "ViolationRepository"]
