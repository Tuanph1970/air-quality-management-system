"""Parser for NetCDF satellite data files (MODIS, CAMS, TROPOMI)."""

from __future__ import annotations

import logging
from typing import List

import numpy as np
import xarray as xr

from ...domain.value_objects.grid_cell import GridCell

logger = logging.getLogger(__name__)


class NetCDFParser:
    """Parses NetCDF / HDF satellite data files into GridCell lists."""

    # ------------------------------------------------------------------
    # MODIS AOD
    # ------------------------------------------------------------------
    def parse_modis_aod(self, filepath: str) -> List[GridCell]:
        """Parse MODIS Aerosol Optical Depth from a NetCDF/HDF file."""
        ds = xr.open_dataset(filepath)

        grid_cells: List[GridCell] = []
        aod_var = "Optical_Depth_Land_And_Ocean"

        if aod_var not in ds:
            logger.warning("Variable %s not found in %s", aod_var, filepath)
            ds.close()
            return grid_cells

        data = ds[aod_var].values
        lats = ds["Latitude"].values
        lons = ds["Longitude"].values

        for i in range(len(lats)):
            for j in range(len(lons)):
                val = data[i, j] if data.ndim == 2 else data[i]
                if not np.isnan(val):
                    grid_cells.append(
                        GridCell(
                            lat=float(lats[i]),
                            lon=float(lons[j]),
                            value=float(val),
                            uncertainty=0.05,
                        )
                    )

        ds.close()
        logger.info("Parsed %d MODIS AOD cells from %s", len(grid_cells), filepath)
        return grid_cells

    # ------------------------------------------------------------------
    # CAMS
    # ------------------------------------------------------------------
    def parse_cams(self, filepath: str, variable: str) -> List[GridCell]:
        """Parse a CAMS NetCDF file for a given variable name."""
        ds = xr.open_dataset(filepath)

        grid_cells: List[GridCell] = []

        if variable not in ds:
            logger.warning("Variable %s not found in %s", variable, filepath)
            ds.close()
            return grid_cells

        data = ds[variable].values

        # Coordinate naming varies between CAMS products.
        if "latitude" in ds.coords:
            lats = ds["latitude"].values
            lons = ds["longitude"].values
        else:
            lats = ds["lat"].values
            lons = ds["lon"].values

        # Collapse the time dimension if present (take first time-step).
        if data.ndim > 2:
            data = data[0]

        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                val = data[i, j]
                if not np.isnan(val):
                    grid_cells.append(
                        GridCell(
                            lat=float(lat),
                            lon=float(lon),
                            value=float(val),
                            uncertainty=0.1,
                        )
                    )

        ds.close()
        logger.info("Parsed %d CAMS cells from %s", len(grid_cells), filepath)
        return grid_cells

    # ------------------------------------------------------------------
    # TROPOMI
    # ------------------------------------------------------------------
    def parse_tropomi(self, filepath: str, variable: str) -> List[GridCell]:
        """Parse a TROPOMI NetCDF file for a given pollutant."""
        ds = xr.open_dataset(filepath)

        grid_cells: List[GridCell] = []
        var_name = f"{variable}_column_number_density"

        if var_name not in ds:
            logger.warning("Variable %s not found in %s", var_name, filepath)
            ds.close()
            return grid_cells

        data = ds[var_name].values
        lats = ds["latitude"].values
        lons = ds["longitude"].values

        for i in range(len(lats)):
            for j in range(len(lons)):
                val = data[i, j] if data.ndim == 2 else data[i]
                if not np.isnan(val):
                    grid_cells.append(
                        GridCell(
                            lat=float(lats[i]),
                            lon=float(lons[j]),
                            value=float(val),
                            uncertainty=0.15,
                        )
                    )

        ds.close()
        logger.info("Parsed %d TROPOMI cells from %s", len(grid_cells), filepath)
        return grid_cells
