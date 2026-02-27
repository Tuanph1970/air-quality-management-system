"""Parser for GeoTIFF raster files."""

from __future__ import annotations

import logging
from typing import List

import numpy as np
import rasterio

from ...domain.value_objects.grid_cell import GridCell

logger = logging.getLogger(__name__)


class GeoTIFFParser:
    """Parses GeoTIFF raster files into GridCell lists."""

    def parse(self, filepath: str, band: int = 1) -> List[GridCell]:
        """Read a single band from a GeoTIFF and return GridCells.

        Parameters
        ----------
        filepath:
            Path to the ``.tif`` file.
        band:
            Band index (1-based) to read.
        """
        grid_cells: List[GridCell] = []

        with rasterio.open(filepath) as src:
            data = src.read(band)
            transform = src.transform
            nodata = src.nodata

            rows, cols = data.shape
            for i in range(rows):
                for j in range(cols):
                    val = data[i, j]
                    if nodata is not None and val == nodata:
                        continue
                    if np.isnan(val):
                        continue

                    # Convert pixel (col, row) → geographic (lon, lat).
                    lon, lat = rasterio.transform.xy(transform, i, j)

                    grid_cells.append(
                        GridCell(
                            lat=float(lat),
                            lon=float(lon),
                            value=float(val),
                            uncertainty=0.0,
                        )
                    )

        logger.info("Parsed %d cells from GeoTIFF %s", len(grid_cells), filepath)
        return grid_cells
