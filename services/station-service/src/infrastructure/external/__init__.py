"""External API clients and adapters."""
from __future__ import annotations

from .station_api_client import StationAPIClient
from .adapters.base_adapter import BaseStationAdapter
from .adapters.generic_adapter import GenericStationAdapter
from .adapters.factory import AdapterFactory

__all__ = [
    "StationAPIClient",
    "BaseStationAdapter",
    "GenericStationAdapter",
    "AdapterFactory",
]
