"""AQI calculation domain service.

Implements the US EPA Air Quality Index algorithm for converting
pollutant concentrations into a standardised 0-500 index.  This is a
stateless domain service — it has no dependencies on repositories or
external systems.

Reference: https://www.airnow.gov/aqi/aqi-basics/

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


# ------------------------------------------------------------------
# EPA AQI breakpoint tables
# ------------------------------------------------------------------
# Each entry: (C_lo, C_hi, I_lo, I_hi)
# Concentrations are in the pollutant's native unit.

_PM25_BREAKPOINTS: List[Tuple[float, float, int, int]] = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

_PM10_BREAKPOINTS: List[Tuple[float, float, int, int]] = [
    (0, 54, 0, 50),
    (55, 154, 51, 100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, 504, 301, 400),
    (505, 604, 401, 500),
]

_CO_BREAKPOINTS: List[Tuple[float, float, int, int]] = [
    (0.0, 4.4, 0, 50),
    (4.5, 9.4, 51, 100),
    (9.5, 12.4, 101, 150),
    (12.5, 15.4, 151, 200),
    (15.5, 30.4, 201, 300),
    (30.5, 40.4, 301, 400),
    (40.5, 50.4, 401, 500),
]

_NO2_BREAKPOINTS: List[Tuple[float, float, int, int]] = [
    (0, 53, 0, 50),
    (54, 100, 51, 100),
    (101, 360, 101, 150),
    (361, 649, 151, 200),
    (650, 1249, 201, 300),
    (1250, 1649, 301, 400),
    (1650, 2049, 401, 500),
]

_SO2_BREAKPOINTS: List[Tuple[float, float, int, int]] = [
    (0, 35, 0, 50),
    (36, 75, 51, 100),
    (76, 185, 101, 150),
    (186, 304, 151, 200),
    (305, 604, 201, 300),
    (605, 804, 301, 400),
    (805, 1004, 401, 500),
]

_O3_BREAKPOINTS: List[Tuple[float, float, int, int]] = [
    (0, 54, 0, 50),
    (55, 70, 51, 100),
    (71, 85, 101, 150),
    (86, 105, 151, 200),
    (106, 200, 201, 300),
    (201, 404, 301, 400),
    (405, 604, 401, 500),
]

_BREAKPOINT_TABLE: Dict[str, List[Tuple[float, float, int, int]]] = {
    "pm25": _PM25_BREAKPOINTS,
    "pm10": _PM10_BREAKPOINTS,
    "co": _CO_BREAKPOINTS,
    "no2": _NO2_BREAKPOINTS,
    "so2": _SO2_BREAKPOINTS,
    "o3": _O3_BREAKPOINTS,
}

# AQI category labels
_AQI_CATEGORIES: List[Tuple[int, int, str]] = [
    (0, 50, "Good"),
    (51, 100, "Moderate"),
    (101, 150, "Unhealthy for Sensitive Groups"),
    (151, 200, "Unhealthy"),
    (201, 300, "Very Unhealthy"),
    (301, 500, "Hazardous"),
]


# ------------------------------------------------------------------
# AQI Calculator (domain service)
# ------------------------------------------------------------------
class AQICalculator:
    """Stateless domain service for AQI computation.

    Implements the US EPA linear interpolation formula::

        AQI = ((I_hi - I_lo) / (C_hi - C_lo)) * (C - C_lo) + I_lo

    where *C* is the pollutant concentration and the breakpoint pair
    ``(C_lo, C_hi, I_lo, I_hi)`` is selected from the relevant table.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_aqi(readings: Dict[str, float]) -> int:
        """Calculate the overall AQI from a set of pollutant readings.

        The overall AQI is the **maximum** of individual sub-indices.

        Parameters
        ----------
        readings:
            Mapping of pollutant name → concentration.
            Keys: ``pm25``, ``pm10``, ``co``, ``no2``, ``so2``, ``o3``.

        Returns
        -------
        int
            AQI value in the 0-500 range.  Returns 0 if no valid
            pollutant data is provided.
        """
        sub_indices: List[int] = []
        for pollutant, concentration in readings.items():
            if pollutant not in _BREAKPOINT_TABLE:
                continue
            if concentration <= 0.0:
                continue
            aqi = AQICalculator._sub_index(pollutant, concentration)
            if aqi is not None:
                sub_indices.append(aqi)

        return max(sub_indices) if sub_indices else 0

    @staticmethod
    def get_dominant_pollutant(readings: Dict[str, float]) -> str:
        """Return the pollutant responsible for the highest AQI sub-index.

        Parameters
        ----------
        readings:
            Mapping of pollutant name → concentration.

        Returns
        -------
        str
            Pollutant name (e.g. ``"pm25"``), or ``""`` if no valid
            data is provided.
        """
        best_pollutant = ""
        best_aqi = -1

        for pollutant, concentration in readings.items():
            if pollutant not in _BREAKPOINT_TABLE:
                continue
            if concentration <= 0.0:
                continue
            aqi = AQICalculator._sub_index(pollutant, concentration)
            if aqi is not None and aqi > best_aqi:
                best_aqi = aqi
                best_pollutant = pollutant

        return best_pollutant

    @staticmethod
    def get_category(aqi: int) -> str:
        """Return the human-readable AQI category label.

        Parameters
        ----------
        aqi:
            AQI value (0-500).

        Returns
        -------
        str
            Category label (e.g. ``"Good"``, ``"Hazardous"``).
        """
        for lo, hi, label in _AQI_CATEGORIES:
            if lo <= aqi <= hi:
                return label
        return "Hazardous" if aqi > 300 else "Good"

    @staticmethod
    def calculate_sub_indices(readings: Dict[str, float]) -> Dict[str, int]:
        """Return individual AQI sub-indices for each pollutant.

        Parameters
        ----------
        readings:
            Mapping of pollutant name → concentration.

        Returns
        -------
        Dict[str, int]
            Mapping of pollutant name → AQI sub-index.
        """
        result: Dict[str, int] = {}
        for pollutant, concentration in readings.items():
            if pollutant not in _BREAKPOINT_TABLE:
                continue
            if concentration <= 0.0:
                result[pollutant] = 0
                continue
            aqi = AQICalculator._sub_index(pollutant, concentration)
            if aqi is not None:
                result[pollutant] = aqi
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _sub_index(pollutant: str, concentration: float) -> Optional[int]:
        """Calculate the AQI sub-index for a single pollutant."""
        breakpoints = _BREAKPOINT_TABLE.get(pollutant)
        if breakpoints is None:
            return None

        for c_lo, c_hi, i_lo, i_hi in breakpoints:
            if c_lo <= concentration <= c_hi:
                aqi = ((i_hi - i_lo) / (c_hi - c_lo)) * (concentration - c_lo) + i_lo
                return round(aqi)

        # Concentration exceeds all breakpoints — cap at 500
        if concentration > breakpoints[-1][1]:
            return 500

        return None
