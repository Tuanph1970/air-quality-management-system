"""Factory service REST API interface."""
from .dependencies import get_event_publisher, get_factory_service, init_event_publisher
from .factory_controller import router
from .routes import app

__all__ = [
    "app",
    "router",
    "get_factory_service",
    "get_event_publisher",
    "init_event_publisher",
]
