"""Sensor domain events (re-exported from shared library).

The canonical event definitions live in ``shared.events.sensor_events``
so that other bounded contexts can import them without depending on this
service.  This module simply re-exports them for convenience within the
sensor service codebase.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from shared.events.sensor_events import (  # noqa: F401
    SensorCalibrated,
    SensorReadingCreated,
    SensorRegistered,
    SensorStatusChanged,
)

__all__ = [
    "SensorRegistered",
    "SensorReadingCreated",
    "SensorCalibrated",
    "SensorStatusChanged",
]
