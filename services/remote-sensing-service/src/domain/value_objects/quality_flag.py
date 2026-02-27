"""Satellite data quality flag enumeration."""

from enum import Enum


class QualityFlag(Enum):
    GOOD = "good"
    MEDIUM = "medium"
    LOW = "low"
    INVALID = "invalid"
