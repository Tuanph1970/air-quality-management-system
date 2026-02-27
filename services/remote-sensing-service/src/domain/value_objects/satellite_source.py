"""Satellite data source enumeration."""

from enum import Enum


class SatelliteSource(Enum):
    MODIS_TERRA = "modis_terra"
    MODIS_AQUA = "modis_aqua"
    TROPOMI_NO2 = "tropomi_no2"
    TROPOMI_SO2 = "tropomi_so2"
    TROPOMI_O3 = "tropomi_o3"
    TROPOMI_CO = "tropomi_co"
    CAMS_PM25 = "cams_pm25"
    CAMS_PM10 = "cams_pm10"
    CAMS_FORECAST = "cams_forecast"
