"""Sensor operational status.

Tracks the current lifecycle state of a sensor device.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from enum import Enum


class SensorStatus(str, Enum):
    """Operational status of a sensor device.

    State transitions
    -----------------
    ::

        ONLINE ──► OFFLINE
        ONLINE ──► CALIBRATING ──► ONLINE
        ONLINE ──► MAINTENANCE ──► ONLINE
        OFFLINE ──► ONLINE
        OFFLINE ──► MAINTENANCE ──► ONLINE
        MAINTENANCE ──► ONLINE
    """

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    CALIBRATING = "CALIBRATING"
    MAINTENANCE = "MAINTENANCE"

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    @property
    def is_active(self) -> bool:
        """Return ``True`` if the sensor is currently collecting readings."""
        return self == self.ONLINE

    @property
    def is_available(self) -> bool:
        """Return ``True`` if the sensor is in a non-terminal state."""
        return self in (self.ONLINE, self.CALIBRATING, self.MAINTENANCE)

    @property
    def can_submit_reading(self) -> bool:
        """Return ``True`` if the sensor can accept new readings."""
        return self == self.ONLINE
