"""AQI Calculator domain service.

Implements the US EPA Air Quality Index (AQI) calculation algorithm.
The AQI converts pollutant concentrations to a scale of 0-500, where:

- 0-50: Good (Green)
- 51-100: Moderate (Yellow)
- 101-150: Unhealthy for Sensitive Groups (Orange)
- 151-200: Unhealthy (Red)
- 201-300: Very Unhealthy (Purple)
- 301-500: Hazardous (Maroon)

References:
    https://www.epa.gov/aqi/how-aqi-works
    https://www.epa.gov/sites/default/files/2016-06/documents/aqi.pdf

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from ..value_objects.aqi_level import AQILevel


# =============================================================================
# US EPA AQI Breakpoints (40 CFR Part 58, Appendix G)
# =============================================================================
# Format: pollutant -> [(C_low, C_high, I_low, I_high), ...]
# C = concentration (μg/m³ or ppm), I = AQI
# =============================================================================

AQI_BREAKPOINTS: Dict[str, list] = {
    # PM2.5 (μg/m³) - 24-hour
    "pm25": [
        (0.0, 12.0, 0, 50),       # Good
        (12.1, 35.4, 51, 100),    # Moderate
        (35.5, 55.4, 101, 150),   # Unhealthy for Sensitive Groups
        (55.5, 150.4, 151, 200),  # Unhealthy
        (150.5, 250.4, 201, 300), # Very Unhealthy
        (250.5, 500.4, 301, 500), # Hazardous
    ],
    # PM10 (μg/m³) - 24-hour
    "pm10": [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 604, 301, 500),
    ],
    # CO (ppm) - 8-hour
    "co": [
        (0.0, 4.4, 0, 50),
        (4.5, 9.4, 51, 100),
        (9.5, 12.4, 101, 150),
        (12.5, 15.4, 151, 200),
        (15.5, 30.4, 201, 300),
        (30.5, 50.4, 301, 500),
    ],
    # NO2 (μg/m³) - 1-hour
    "no2": [
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 2049, 301, 500),
    ],
    # SO2 (μg/m³) - 1-hour
    "so2": [
        (0, 35, 0, 50),
        (36, 75, 51, 100),
        (76, 185, 101, 150),
        (186, 304, 151, 200),
        (305, 604, 201, 300),
        (605, 1004, 301, 500),
    ],
    # O3 (μg/m³) - 8-hour (converted from ppb: 1 ppb ≈ 2.0 μg/m³)
    "o3": [
        (0, 108, 0, 50),      # 0-54 ppb
        (109, 140, 51, 100),  # 55-70 ppb
        (141, 170, 101, 150), # 71-85 ppb
        (171, 210, 151, 200), # 86-105 ppb
        (211, 410, 201, 300), # 106-200 ppb
        (411, 610, 301, 500), # 201-300 ppb
    ],
}

# AQI Category definitions
AQI_CATEGORIES = {
    (0, 50): {
        "level": AQILevel.GOOD,
        "color": "#00E400",
        "color_name": "Green",
        "health_message": "Air quality is satisfactory, and air pollution poses little or no risk.",
        "caution_message": "None",
    },
    (51, 100): {
        "level": AQILevel.MODERATE,
        "color": "#FFFF00",
        "color_name": "Yellow",
        "health_message": "Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.",
        "caution_message": "Unusually sensitive people should consider reducing prolonged or heavy outdoor exertion.",
    },
    (101, 150): {
        "level": AQILevel.UNHEALTHY_SENSITIVE,
        "color": "#FF7E00",
        "color_name": "Orange",
        "health_message": "Members of sensitive groups may experience health effects. The general public is less likely to be affected.",
        "caution_message": "People with heart or lung disease, older adults, children, and people of lower socioeconomic status should reduce prolonged or heavy outdoor exertion.",
    },
    (151, 200): {
        "level": AQILevel.UNHEALTHY,
        "color": "#FF0000",
        "color_name": "Red",
        "health_message": "Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.",
        "caution_message": "People with heart or lung disease, older adults, children, and people of lower socioeconomic status should avoid prolonged or heavy outdoor exertion. Everyone else should reduce prolonged or heavy outdoor exertion.",
    },
    (201, 300): {
        "level": AQILevel.VERY_UNHEALTHY,
        "color": "#8F3F97",
        "color_name": "Purple",
        "health_message": "Health alert: The risk of health effects is increased for everyone.",
        "caution_message": "People with heart or lung disease, older adults, children, and people of lower socioeconomic status should avoid all outdoor exertion. Everyone else should avoid prolonged or heavy outdoor exertion.",
    },
    (301, 500): {
        "level": AQILevel.HAZARDOUS,
        "color": "#7E0023",
        "color_name": "Maroon",
        "health_message": "Health warning of emergency conditions: everyone is more likely to be affected.",
        "caution_message": "Everyone should avoid all physical activity outdoors.",
    },
}


@dataclass
class AQIResult:
    """Result of AQI calculation."""

    aqi_value: int
    level: AQILevel
    category: str
    color: str
    health_message: str
    caution_message: str
    dominant_pollutant: str


class AQICalculator:
    """US EPA AQI Calculator domain service.

    Calculates the Air Quality Index (AQI) from pollutant concentrations
    using the EPA's breakpoint table method.
    """

    def __init__(self):
        self.breakpoints = AQI_BREAKPOINTS
        self.categories = AQI_CATEGORIES

    def calculate_aqi(self, pollutant: str, concentration: float) -> int:
        """Calculate AQI for a single pollutant.

        Uses the EPA AQI formula:
            I = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low

        Parameters
        ----------
        pollutant:
            Pollutant code (pm25, pm10, co, no2, so2, o3)
        concentration:
            Measured concentration in appropriate units

        Returns
        -------
        int
            AQI value (0-500), or -1 if pollutant not recognized

        Raises
        ------
        ValueError
            If concentration is negative
        """
        if concentration < 0:
            raise ValueError(f"Concentration must be non-negative, got {concentration}")

        pollutant_lower = pollutant.lower()
        if pollutant_lower not in self.breakpoints:
            raise ValueError(f"Unknown pollutant: {pollutant}")

        breakpoint_table = self.breakpoints[pollutant_lower]

        # Find the appropriate breakpoint range
        for c_low, c_high, i_low, i_high in breakpoint_table:
            if c_low <= concentration <= c_high:
                # Linear interpolation formula
                aqi = ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low) + i_low
                return round(aqi)

        # Concentration exceeds highest breakpoint (capped at 500)
        return 500

    def calculate_composite_aqi(self, pollutants: Dict[str, float]) -> AQIResult:
        """Calculate composite AQI from multiple pollutant concentrations.

        The overall AQI is the maximum of individual pollutant AQIs.
        The pollutant causing the maximum is the "dominant pollutant".

        Parameters
        ----------
        pollutants:
            Dict mapping pollutant codes to concentrations

        Returns
        -------
        AQIResult
            Complete AQI result with category, color, and health messages
        """
        if not pollutants:
            return AQIResult(
                aqi_value=0,
                level=AQILevel.GOOD,
                category="Good",
                color="#00E400",
                health_message="No data available.",
                caution_message="None",
                dominant_pollutant="none",
            )

        # Calculate individual AQI for each pollutant
        individual_aqis: Dict[str, int] = {}
        for pollutant, concentration in pollutants.items():
            try:
                aqi = self.calculate_aqi(pollutant, concentration)
                individual_aqis[pollutant] = aqi
            except ValueError:
                continue  # Skip unknown pollutants

        if not individual_aqis:
            return AQIResult(
                aqi_value=0,
                level=AQILevel.GOOD,
                category="Good",
                color="#00E400",
                health_message="No valid pollutant data available.",
                caution_message="None",
                dominant_pollutant="none",
            )

        # Find the dominant pollutant (highest AQI)
        dominant_pollutant = max(individual_aqis, key=individual_aqis.get)
        aqi_value = individual_aqis[dominant_pollutant]

        # Get category information
        category_info = self._get_category(aqi_value)

        return AQIResult(
            aqi_value=aqi_value,
            level=category_info["level"],
            category=category_info["level"].value.replace("_", " "),
            color=category_info["color"],
            health_message=category_info["health_message"],
            caution_message=category_info["caution_message"],
            dominant_pollutant=dominant_pollutant,
        )

    def get_aqi_category(self, aqi: int) -> str:
        """Get the AQI category name for an AQI value.

        Parameters
        ----------
        aqi:
            AQI value (0-500)

        Returns
        -------
        str
            Category name (e.g., "Good", "Moderate", "Unhealthy")
        """
        category_info = self._get_category(aqi)
        return category_info["level"].value.replace("_", " ")

    def get_aqi_color(self, aqi: int) -> str:
        """Get the color code for an AQI value.

        Parameters
        ----------
        aqi:
            AQI value (0-500)

        Returns
        -------
        str
            Hex color code (e.g., "#00E400" for Good)
        """
        category_info = self._get_category(aqi)
        return category_info["color"]

    def get_health_message(self, aqi: int) -> str:
        """Get the health message for an AQI value.

        Parameters
        ----------
        aqi:
            AQI value (0-500)

        Returns
        -------
        str
            Health impact message
        """
        category_info = self._get_category(aqi)
        return category_info["health_message"]

    def get_caution_message(self, aqi: int) -> str:
        """Get the caution statement for an AQI value.

        Parameters
        ----------
        aqi:
            AQI value (0-500)

        Returns
        -------
        str
            Caution statement for sensitive groups
        """
        category_info = self._get_category(aqi)
        return category_info["caution_message"]

    def _get_category(self, aqi: int) -> dict:
        """Get category information for an AQI value.

        Parameters
        ----------
        aqi:
            AQI value (0-500)

        Returns
        -------
        dict
            Category info including level, color, and messages
        """
        # Cap at 500
        aqi = min(aqi, 500)

        for (low, high), info in self.categories.items():
            if low <= aqi <= high:
                return info

        # Default to Hazardous for anything above 500
        return self.categories[(301, 500)]

    def get_all_pollutant_aqis(self, pollutants: Dict[str, float]) -> Dict[str, int]:
        """Calculate individual AQI for each pollutant.

        Parameters
        ----------
        pollutants:
            Dict mapping pollutant codes to concentrations

        Returns
        -------
        dict
            Dict mapping pollutant codes to their individual AQI values
        """
        result = {}
        for pollutant, concentration in pollutants.items():
            try:
                result[pollutant] = self.calculate_aqi(pollutant, concentration)
            except ValueError:
                continue
        return result
