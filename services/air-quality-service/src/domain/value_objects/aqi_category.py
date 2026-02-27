"""AQI Category value object.

Encapsulates all information about an AQI category including level,
color codes, and health messages.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .aqi_level import AQILevel


@dataclass(frozen=True)
class AQICategory:
    """Value object representing an AQI category.

    Attributes
    ----------
    level:
        The AQI level enum value
    min_aqi:
        Minimum AQI value for this category
    max_aqi:
        Maximum AQI value for this category
    color_hex:
        Hex color code for display
    color_name:
        Human-readable color name
    health_message:
        Health impact description
    caution_message:
        Caution statement for sensitive groups
    """

    level: AQILevel
    min_aqi: int
    max_aqi: int
    color_hex: str
    color_name: str
    health_message: str
    caution_message: str

    def contains(self, aqi: int) -> bool:
        """Check if an AQI value falls within this category."""
        return self.min_aqi <= aqi <= self.max_aqi

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "level": self.level.value,
            "min_aqi": self.min_aqi,
            "max_aqi": self.max_aqi,
            "color_hex": self.color_hex,
            "color_name": self.color_name,
            "health_message": self.health_message,
            "caution_message": self.caution_message,
        }


# Predefined AQI categories following US EPA standards
AQI_CATEGORIES = {
    AQILevel.GOOD: AQICategory(
        level=AQILevel.GOOD,
        min_aqi=0,
        max_aqi=50,
        color_hex="#00E400",
        color_name="Green",
        health_message="Air quality is satisfactory, and air pollution poses little or no risk.",
        caution_message="None",
    ),
    AQILevel.MODERATE: AQICategory(
        level=AQILevel.MODERATE,
        min_aqi=51,
        max_aqi=100,
        color_hex="#FFFF00",
        color_name="Yellow",
        health_message="Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.",
        caution_message="Unusually sensitive people should consider reducing prolonged or heavy outdoor exertion.",
    ),
    AQILevel.UNHEALTHY_SENSITIVE: AQICategory(
        level=AQILevel.UNHEALTHY_SENSITIVE,
        min_aqi=101,
        max_aqi=150,
        color_hex="#FF7E00",
        color_name="Orange",
        health_message="Members of sensitive groups may experience health effects. The general public is less likely to be affected.",
        caution_message="People with heart or lung disease, older adults, children, and people of lower socioeconomic status should reduce prolonged or heavy outdoor exertion.",
    ),
    AQILevel.UNHEALTHY: AQICategory(
        level=AQILevel.UNHEALTHY,
        min_aqi=151,
        max_aqi=200,
        color_hex="#FF0000",
        color_name="Red",
        health_message="Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.",
        caution_message="People with heart or lung disease, older adults, children, and people of lower socioeconomic status should avoid prolonged or heavy outdoor exertion. Everyone else should reduce prolonged or heavy outdoor exertion.",
    ),
    AQILevel.VERY_UNHEALTHY: AQICategory(
        level=AQILevel.VERY_UNHEALTHY,
        min_aqi=201,
        max_aqi=300,
        color_hex="#8F3F97",
        color_name="Purple",
        health_message="Health alert: The risk of health effects is increased for everyone.",
        caution_message="People with heart or lung disease, older adults, children, and people of lower socioeconomic status should avoid all outdoor exertion. Everyone else should avoid prolonged or heavy outdoor exertion.",
    ),
    AQILevel.HAZARDOUS: AQICategory(
        level=AQILevel.HAZARDOUS,
        min_aqi=301,
        max_aqi=500,
        color_hex="#7E0023",
        color_name="Maroon",
        health_message="Health warning of emergency conditions: everyone is more likely to be affected.",
        caution_message="Everyone should avoid all physical activity outdoors.",
    ),
}


def get_category_for_aqi(aqi: int) -> AQICategory:
    """Get the AQI category for a given AQI value.

    Parameters
    ----------
    aqi:
        AQI value (0-500)

    Returns
    -------
    AQICategory
        The matching category, or HAZARDOUS for values > 500
    """
    aqi = min(aqi, 500)  # Cap at 500

    for category in AQI_CATEGORIES.values():
        if category.contains(aqi):
            return category

    # Default to Hazardous
    return AQI_CATEGORIES[AQILevel.HAZARDOUS]


def get_all_categories() -> list:
    """Get all AQI categories.

    Returns
    -------
    list
        List of all AQICategory objects
    """
    return list(AQI_CATEGORIES.values())
