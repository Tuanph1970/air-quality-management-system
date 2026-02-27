"""Remote Sensing external API clients.

Clients are imported lazily to avoid hard failures when optional
native libraries (cdsapi, xarray, etc.) are not installed locally.
Use direct imports in application code::

    from src.infrastructure.external.copernicus_cams_client import CopernicusCAMSClient
"""

__all__ = [
    "CopernicusCAMSClient",
    "NASAEarthdataClient",
    "SentinelHubClient",
    "SensorServiceClient",
]
