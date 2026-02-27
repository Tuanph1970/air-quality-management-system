"""Remote Sensing data parsers.

Parsers are imported lazily to avoid hard failures when optional
native libraries (xarray, rasterio, etc.) are not installed locally.
Use direct imports in application code::

    from src.infrastructure.parsers.netcdf_parser import NetCDFParser
"""

__all__ = [
    "NetCDFParser",
    "ExcelParser",
    "ValidationResult",
    "GeoTIFFParser",
]
