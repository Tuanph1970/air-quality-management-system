"""Parser for Excel data files (historical readings, factory records)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of an Excel file format validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    row_count: int
    columns_found: List[str]


class ExcelParser:
    """Parses and validates Excel files for the remote-sensing service."""

    HISTORICAL_READINGS_COLUMNS = [
        "timestamp",
        "sensor_id",
        "location_id",
        "latitude",
        "longitude",
        "pm25",
        "pm10",
        "co2",
        "no2",
        "temperature",
        "humidity",
    ]

    FACTORY_RECORDS_COLUMNS = [
        "factory_name",
        "registration_number",
        "industry_type",
        "address",
        "latitude",
        "longitude",
        "contact_email",
        "pm25_limit",
        "pm10_limit",
        "co2_limit",
        "nox_limit",
    ]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_format(
        self, filepath: str, expected_columns: List[str]
    ) -> ValidationResult:
        """Validate an Excel file against expected column schema."""
        errors: List[str] = []
        warnings: List[str] = []

        try:
            df = pd.read_excel(filepath)
            columns_found = df.columns.tolist()

            missing = set(expected_columns) - set(
                c.lower().strip() for c in columns_found
            )
            if missing:
                errors.append(f"Missing required columns: {missing}")

            extra = set(c.lower().strip() for c in columns_found) - set(
                expected_columns
            )
            if extra:
                warnings.append(f"Extra columns will be ignored: {extra}")

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                row_count=len(df),
                columns_found=columns_found,
            )
        except Exception as exc:
            return ValidationResult(
                is_valid=False,
                errors=[f"Failed to read file: {exc}"],
                warnings=[],
                row_count=0,
                columns_found=[],
            )

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    def parse_historical_readings(self, filepath: str) -> List[Dict]:
        """Parse historical air quality readings from an Excel file."""
        df = pd.read_excel(filepath)
        df.columns = df.columns.str.lower().str.strip()

        records: List[Dict] = []
        for _, row in df.iterrows():
            record = {
                "timestamp": pd.to_datetime(row.get("timestamp")),
                "sensor_id": str(row.get("sensor_id", "")),
                "location_id": str(row.get("location_id", "")),
                "latitude": float(row.get("latitude", 0)),
                "longitude": float(row.get("longitude", 0)),
                "pm25": (
                    float(row.get("pm25"))
                    if pd.notna(row.get("pm25"))
                    else None
                ),
                "pm10": (
                    float(row.get("pm10"))
                    if pd.notna(row.get("pm10"))
                    else None
                ),
                "co2": (
                    float(row.get("co2"))
                    if pd.notna(row.get("co2"))
                    else None
                ),
                "no2": (
                    float(row.get("no2"))
                    if pd.notna(row.get("no2"))
                    else None
                ),
                "temperature": (
                    float(row.get("temperature"))
                    if pd.notna(row.get("temperature"))
                    else None
                ),
                "humidity": (
                    float(row.get("humidity"))
                    if pd.notna(row.get("humidity"))
                    else None
                ),
            }
            records.append(record)

        logger.info("Parsed %d historical readings from %s", len(records), filepath)
        return records

    def parse_factory_records(self, filepath: str) -> List[Dict]:
        """Parse factory records from an Excel file."""
        df = pd.read_excel(filepath)
        df.columns = df.columns.str.lower().str.strip()

        records: List[Dict] = []
        for _, row in df.iterrows():
            record = {
                "name": str(row.get("factory_name", "")),
                "registration_number": str(row.get("registration_number", "")),
                "industry_type": str(row.get("industry_type", "")),
                "address": str(row.get("address", "")),
                "latitude": float(row.get("latitude", 0)),
                "longitude": float(row.get("longitude", 0)),
                "contact_email": str(row.get("contact_email", "")),
                "emission_limits": {
                    "pm25": float(row.get("pm25_limit", 100)),
                    "pm10": float(row.get("pm10_limit", 150)),
                    "co2": float(row.get("co2_limit", 1000)),
                    "nox": float(row.get("nox_limit", 200)),
                },
            }
            records.append(record)

        logger.info("Parsed %d factory records from %s", len(records), filepath)
        return records
