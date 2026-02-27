"""Messaging for Air Quality Service."""
from .event_consumers import AirQualityEventHandler, set_cache_for_handler

__all__ = ["AirQualityEventHandler", "set_cache_for_handler"]
