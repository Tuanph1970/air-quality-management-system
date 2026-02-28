#!/usr/bin/env python3
"""Generate sample Excel files for testing data import functionality.

This script creates realistic Excel files for testing the
historical readings and factory records import features.

Usage:
    python generate-test-excel.py [--output-dir DIR] [--rows N]

Examples:
    python generate-test-excel.py
    python generate-test-excel.py --output-dir ./test_files --rows 500
"""
import argparse
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system("pip install pandas openpyxl numpy")
    import pandas as pd
    import numpy as np


# Sample data for generating realistic test files
SAMPLE_FACTORY_NAMES = [
    "Steel Plant Alpha",
    "Chemical Works Beta",
    "Cement Factory Gamma",
    "Power Station Delta",
    "Refinery Epsilon",
    "Manufacturing Plant Zeta",
    "Industrial Complex Eta",
    "Processing Facility Theta",
    "Factory Complex Iota",
    "Production Plant Kappa",
    "Heavy Industries Lambda",
    "Light Manufacturing Mu",
    "Textile Mill Nu",
    "Paper Mill Xi",
    "Food Processing Omicron",
]

INDUSTRY_TYPES = [
    "steel",
    "chemical",
    "cement",
    "power_generation",
    "refinery",
    "manufacturing",
    "textile",
    "paper",
    "food_processing",
    "electronics",
]

POLLUTANT_LEVELS = {
    "steel": {"pm25": (40, 80), "pm10": (80, 150), "co2": (400, 800), "no2": (15, 40)},
    "chemical": {"pm25": (25, 60), "pm10": (50, 100), "co2": (300, 600), "no2": (20, 50)},
    "cement": {"pm25": (50, 100), "pm10": (100, 200), "co2": (500, 1000), "no2": (10, 30)},
    "power_generation": {"pm25": (30, 70), "pm10": (60, 120), "co2": (600, 1200), "no2": (25, 60)},
    "refinery": {"pm25": (35, 75), "pm10": (70, 140), "co2": (450, 900), "no2": (30, 70)},
    "manufacturing": {"pm25": (20, 50), "pm10": (40, 90), "co2": (200, 400), "no2": (10, 25)},
    "textile": {"pm25": (15, 40), "pm10": (30, 70), "co2": (150, 300), "no2": (5, 15)},
    "paper": {"pm25": (25, 55), "pm10": (50, 100), "co2": (250, 500), "no2": (15, 35)},
    "food_processing": {"pm25": (10, 30), "pm10": (20, 50), "co2": (100, 200), "no2": (5, 12)},
    "electronics": {"pm25": (8, 25), "pm10": (15, 40), "co2": (80, 150), "no2": (3, 10)},
}

STATUS_OPTIONS = ["active", "active", "active", "active", "warning", "suspended"]


def generate_historical_readings(
    num_rows: int = 100,
    num_sensors: int = 5,
    start_date: datetime = None,
) -> pd.DataFrame:
    """Generate historical air quality readings.
    
    Creates realistic sensor data with:
    - Timestamps at hourly intervals
    - Multiple sensors at different locations
    - Correlated pollutant values
    - Realistic diurnal patterns
    - Some anomalies for testing validation
    """
    if start_date is None:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    # Ho Chi Minh City area coordinates
    base_lat = 10.7769
    base_lon = 106.7009
    
    # Generate sensor locations
    sensors = []
    for i in range(num_sensors):
        sensors.append({
            "id": f"sensor_{i+1:03d}",
            "lat": base_lat + random.uniform(-0.3, 0.3),
            "lon": base_lon + random.uniform(-0.3, 0.3),
            "base_pm25": random.uniform(25, 50),
            "base_pm10": random.uniform(50, 100),
        })
    
    data = []
    current_time = start_date
    
    for _ in range(num_rows):
        sensor = random.choice(sensors)
        
        # Add diurnal pattern (higher during rush hours)
        hour = current_time.hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
            multiplier = random.uniform(1.3, 1.8)
        elif 0 <= hour <= 5:  # Night
            multiplier = random.uniform(0.6, 0.8)
        else:
            multiplier = random.uniform(0.9, 1.2)
        
        # Add day-of-week pattern (lower on weekends)
        if current_time.weekday() >= 5:  # Weekend
            multiplier *= random.uniform(0.7, 0.9)
        
        # Generate pollutant values with correlation
        pm25 = sensor["base_pm25"] * multiplier + random.gauss(0, 5)
        pm10 = pm25 * random.uniform(1.8, 2.2) + random.gauss(0, 10)
        co2 = pm25 * random.uniform(8, 12) + random.gauss(0, 50)
        no2 = pm25 * random.uniform(0.3, 0.5) + random.gauss(0, 3)
        
        # Temperature and humidity (inverse correlation)
        temperature = 28 + random.gauss(0, 3) - (hour - 14) * 0.3
        humidity = 65 + random.gauss(0, 10) + (hour - 14) * 0.5
        
        # Occasionally add anomalies (5% of data)
        if random.random() < 0.05:
            pm25 *= random.uniform(2, 4)  # Spike
        
        data.append({
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "location_id": sensor["id"],
            "latitude": round(sensor["lat"], 4),
            "longitude": round(sensor["lon"], 4),
            "pm25": round(max(5, pm25), 1),
            "pm10": round(max(10, pm10), 1),
            "co2": round(max(300, co2), 0),
            "no2": round(max(1, no2), 1),
            "temperature": round(max(15, min(40, temperature)), 1),
            "humidity": round(max(30, min(95, humidity)), 1),
        })
        
        current_time += timedelta(hours=random.randint(1, 6))
    
    return pd.DataFrame(data)


def generate_factory_records(
    num_factories: int = 20,
) -> pd.DataFrame:
    """Generate factory emission records.
    
    Creates realistic factory data with:
    - Various industry types
    - Realistic emission limits based on industry
    - Geographic distribution
    - Different status values
    """
    base_lat = 10.7769
    base_lon = 106.7009
    
    data = []
    used_names = set()
    
    for i in range(num_factories):
        # Generate unique factory name
        while True:
            name = random.choice(SAMPLE_FACTORY_NAMES)
            suffix = f" #{i+1}" if i >= len(SAMPLE_FACTORY_NAMES) else ""
            full_name = f"{name}{suffix}"
            if full_name not in used_names:
                used_names.add(full_name)
                break
        
        industry_type = random.choice(INDUSTRY_TYPES)
        limits = POLLUTANT_LEVELS.get(industry_type, POLLUTANT_LEVELS["manufacturing"])
        
        # Generate location (spread around the city)
        lat = base_lat + random.uniform(-0.4, 0.4)
        lon = base_lon + random.uniform(-0.4, 0.4)
        
        # Emission limits based on industry
        pm25_limit = random.uniform(*limits["pm25"])
        pm10_limit = random.uniform(*limits["pm10"])
        
        data.append({
            "factory_name": full_name,
            "registration_number": f"REG-{2024001 + i:06d}",
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "industry_type": industry_type,
            "pm25_limit": round(pm25_limit, 1),
            "pm10_limit": round(pm10_limit, 1),
            "status": random.choice(STATUS_OPTIONS),
        })
    
    return pd.DataFrame(data)


def create_excel_with_formatting(
    df: pd.DataFrame,
    filename: str,
    sheet_name: str = "Data",
    include_instructions: bool = True,
):
    """Create Excel file with professional formatting."""
    # Create Excel writer with openpyxl engine
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Add instructions row if requested
        if include_instructions:
            # Insert row at top for instructions
            worksheet.insert_rows(1)
            
            # Merge cells for instruction header
            max_col = chr(64 + len(df.columns))
            worksheet.merge_cells(f"A1:{max_col}1")
            
            # Format instruction cell
            instruction_cell = worksheet["A1"]
            instruction_cell.value = (
                f"Template: {sheet_name.replace('_', ' ').title()} - "
                f"Fill in your data below. Keep column names unchanged. "
                f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            instruction_cell.font = instruction_cell.font.copy(
                bold=True,
                color="FF0066CC",
                size=11,
            )
            instruction_cell.alignment = instruction_cell.alignment.copy(
                horizontal="center"
            )
            worksheet.row_dimensions[1].height = 25
        
        # Format header row
        header_row = 2 if include_instructions else 1
        for cell in worksheet[header_row]:
            cell.font = cell.font.copy(bold=True, color="FFFFFF")
            cell.fill = cell.fill.__class__(start_color="4472C4", fill_type="solid")
            cell.alignment = cell.alignment.copy(horizontal="center", vertical="center")
            worksheet.row_dimensions[header_row].height = 20
        
        # Format data columns
        for col_idx, col_name in enumerate(df.columns, 1):
            col_letter = chr(64 + col_idx)
            
            # Set column widths based on content
            max_length = max(
                len(str(col_name)),
                df[col_name].astype(str).max().__len__() + 2
            )
            worksheet.column_dimensions[col_letter].width = min(max_length, 25)
            
            # Apply number formatting for numeric columns
            if df[col_name].dtype in ["float64", "int64"]:
                for row_idx in range(header_row + 1, header_row + 1 + len(df)):
                    cell = worksheet[f"{col_letter}{row_idx}"]
                    cell.number_format = "0.00" if "lat" in col_name.lower() or "limit" in col_name.lower() else "0"
        
        # Add alternating row colors
        for row_idx in range(header_row + 1, header_row + 1 + len(df), 2):
            for col_idx in range(1, len(df.columns) + 1):
                cell = worksheet[f"{chr(64 + col_idx)}{row_idx}"]
                cell.fill = cell.fill.__class__(start_color="F2F2F2", fill_type="solid")
        
        # Add borders
        from openpyxl.styles import Border, Side
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        
        for row in worksheet.iter_rows(
            min_row=header_row,
            max_row=header_row + len(df),
            min_col=1,
            max_col=len(df.columns),
        ):
            for cell in row:
                cell.border = thin_border
    
    print(f"✓ Created: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate sample Excel files for testing data import"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: scripts/test_excel_files)",
    )
    parser.add_argument(
        "--readings-rows",
        type=int,
        default=200,
        help="Number of reading rows to generate",
    )
    parser.add_argument(
        "--factories",
        type=int,
        default=20,
        help="Number of factory records to generate",
    )
    parser.add_argument(
        "--sensors",
        type=int,
        default=5,
        help="Number of sensors for readings",
    )
    
    args = parser.parse_args()
    
    # Set output directory
    if args.output_dir is None:
        output_dir = Path(__file__).parent / "test_excel_files"
    else:
        output_dir = Path(args.output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Generating Sample Excel Test Files")
    print("=" * 60)
    
    # Generate historical readings
    print(f"\n1. Generating {args.readings_rows} historical readings...")
    readings_df = generate_historical_readings(
        num_rows=args.readings_rows,
        num_sensors=args.sensors,
    )
    
    readings_file = output_dir / "historical_readings_sample.xlsx"
    create_excel_with_formatting(
        readings_df,
        str(readings_file),
        sheet_name="Historical Readings",
    )
    
    # Print readings summary
    print(f"   Sensors: {args.sensors}")
    print(f"   Date range: {readings_df['timestamp'].min()} to {readings_df['timestamp'].max()}")
    print(f"   PM2.5 range: {readings_df['pm25'].min():.1f} - {readings_df['pm25'].max():.1f} µg/m³")
    print(f"   PM10 range: {readings_df['pm10'].min():.1f} - {readings_df['pm10'].max():.1f} µg/m³")
    
    # Generate factory records
    print(f"\n2. Generating {args.factories} factory records...")
    factories_df = generate_factory_records(num_factories=args.factories)
    
    factories_file = output_dir / "factory_records_sample.xlsx"
    create_excel_with_formatting(
        factories_df,
        str(factories_file),
        sheet_name="Factory Records",
    )
    
    # Print factory summary
    print(f"   Industry types: {factories_df['industry_type'].nunique()}")
    print(f"   Status distribution:")
    for status, count in factories_df["status"].value_counts().items():
        print(f"      {status}: {count}")
    
    # Generate edge case file
    print(f"\n3. Generating edge case test file...")
    edge_cases_df = generate_historical_readings(
        num_rows=50,
        num_sensors=3,
        start_date=datetime.utcnow() - timedelta(days=7),
    )
    
    # Add some edge cases
    edge_cases_df.loc[0, "pm25"] = 0  # Zero value
    edge_cases_df.loc[1, "pm25"] = 500  # Very high value
    edge_cases_df.loc[2, "pm25"] = -10  # Negative (invalid)
    edge_cases_df.loc[3, "latitude"] = 100  # Invalid coordinate
    edge_cases_df.loc[4, "timestamp"] = "invalid-date"  # Invalid date
    
    edge_cases_file = output_dir / "edge_cases_test.xlsx"
    create_excel_with_formatting(
        edge_cases_df,
        str(edge_cases_file),
        sheet_name="Edge Cases",
    )
    
    print(f"   Includes: zero values, extreme values, invalid data")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nGenerated files in: {output_dir}")
    print(f"  1. {readings_file.name}")
    print(f"  2. {factories_file.name}")
    print(f"  3. {edge_cases_file.name}")
    
    print(f"\nUsage:")
    print(f"  - Upload these files via the Data Sources page")
    print(f"  - Use for testing import validation and error handling")
    print(f"  - Edge cases file tests error detection")
    
    print(f"\n✓ Sample Excel generation complete!")


if __name__ == "__main__":
    main()
