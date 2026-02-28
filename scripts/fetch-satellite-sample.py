#!/usr/bin/env python3
"""Fetch sample satellite data for testing and development.

This script fetches sample satellite data from various sources
(CAMS, MODIS, TROPOMI) for a test city and stores it as JSON
for offline testing and development.

Usage:
    python fetch-satellite-sample.py [--city CITY] [--days DAYS]

Examples:
    python fetch-satellite-sample.py --city hcmc --days 7
    python fetch-satellite-sample.py --city hanoi
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system("pip install requests numpy")
    import requests
    import numpy as np


# City bounding boxes
CITY_BBOXES = {
    "hcmc": {
        "name": "Ho Chi Minh City",
        "north": 11.2,
        "south": 10.3,
        "east": 107.1,
        "west": 106.3,
        "center": (10.7769, 106.7009),
    },
    "hanoi": {
        "name": "Hanoi",
        "north": 21.4,
        "south": 20.9,
        "east": 106.1,
        "west": 105.5,
        "center": (21.028, 105.854),
    },
    "danang": {
        "name": "Da Nang",
        "north": 16.3,
        "south": 15.9,
        "east": 108.4,
        "west": 107.9,
        "center": (16.054, 108.202),
    },
    "test": {
        "name": "Test Area",
        "north": 11.0,
        "south": 10.0,
        "east": 107.0,
        "west": 106.0,
        "center": (10.5, 106.5),
    },
}


def generate_mock_cams_data(
    bbox: Dict,
    date: str,
    variable: str = "pm2p5",
) -> Dict:
    """Generate mock CAMS forecast data.
    
    Creates realistic-looking CAMS data for testing without
    requiring actual API access.
    """
    center_lat = (bbox["north"] + bbox["south"]) / 2
    center_lon = (bbox["east"] + bbox["west"]) / 2
    
    # Generate grid cells (simplified 10x10 grid)
    grid_cells = []
    for i in range(10):
        for j in range(10):
            lat = bbox["south"] + (bbox["north"] - bbox["south"]) * i / 9
            lon = bbox["west"] + (bbox["east"] - bbox["west"]) * j / 9
            
            # Generate realistic PM2.5 values with spatial correlation
            base_value = 25 + np.random.normal(0, 5)
            # Add urban center effect
            dist_from_center = np.sqrt((lat - center_lat)**2 + (lon - center_lon)**2)
            urban_effect = max(0, 20 - dist_from_center * 5)
            
            value = max(5, base_value + urban_effect + np.random.normal(0, 3))
            
            grid_cells.append({
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "value": round(value, 2),
                "uncertainty": round(np.random.uniform(0.1, 0.3), 3),
            })
    
    return {
        "id": str(uuid4()),
        "source": "cams_pm25",
        "data_type": "PM25",
        "observation_time": f"{date}T00:00:00Z",
        "fetch_time": datetime.utcnow().isoformat() + "Z",
        "bbox": bbox,
        "grid_cells": grid_cells,
        "grid_cell_count": len(grid_cells),
        "average_value": round(np.mean([c["value"] for c in grid_cells]), 2),
        "quality_flag": "good",
        "metadata": {
            "forecast_hours": [0, 6, 12, 18, 24],
            "model": "CAMS Global",
            "resolution": "40km",
        },
    }


def generate_mock_modis_data(
    bbox: Dict,
    date: str,
) -> Dict:
    """Generate mock MODIS AOD data."""
    center_lat = (bbox["north"] + bbox["south"]) / 2
    center_lon = (bbox["east"] + bbox["west"]) / 2
    
    grid_cells = []
    for i in range(8):
        for j in range(8):
            lat = bbox["south"] + (bbox["north"] - bbox["south"]) * i / 7
            lon = bbox["west"] + (bbox["east"] - bbox["west"]) * j / 7
            
            # AOD values typically 0-1, higher near urban areas
            base_aod = 0.3 + np.random.normal(0, 0.1)
            dist_from_center = np.sqrt((lat - center_lat)**2 + (lon - center_lon)**2)
            urban_effect = max(0, 0.3 - dist_from_center * 0.05)
            
            aod = max(0.05, min(1.5, base_aod + urban_effect + np.random.normal(0, 0.05)))
            
            grid_cells.append({
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "value": round(aod, 4),
                "uncertainty": round(np.random.uniform(0.05, 0.15), 4),
            })
    
    return {
        "id": str(uuid4()),
        "source": "modis_terra",
        "data_type": "AOD",
        "observation_time": f"{date}T02:30:00Z",
        "fetch_time": datetime.utcnow().isoformat() + "Z",
        "bbox": bbox,
        "grid_cells": grid_cells,
        "grid_cell_count": len(grid_cells),
        "average_value": round(np.mean([c["value"] for c in grid_cells]), 4),
        "quality_flag": "good" if np.mean([c["value"] for c in grid_cells]) < 0.5 else "medium",
        "metadata": {
            "product": "MOD04_L2",
            "platform": "Terra",
            "resolution": "10km",
            "cloud_coverage": round(np.random.uniform(5, 30), 1),
        },
    }


def generate_mock_tropomi_data(
    bbox: Dict,
    date: str,
    pollutant: str = "NO2",
) -> Dict:
    """Generate mock TROPOMI trace gas data."""
    center_lat = (bbox["north"] + bbox["south"]) / 2
    center_lon = (bbox["east"] + bbox["west"]) / 2
    
    grid_cells = []
    for i in range(12):
        for j in range(12):
            lat = bbox["south"] + (bbox["north"] - bbox["south"]) * i / 11
            lon = bbox["west"] + (bbox["east"] - bbox["west"]) * j / 10
            
            # NO2 tropospheric column (mol/m²)
            base_no2 = 0.0001 + np.random.normal(0, 0.00003)
            dist_from_center = np.sqrt((lat - center_lat)**2 + (lon - center_lon)**2)
            urban_effect = max(0, 0.00015 - dist_from_center * 0.00002)
            
            no2 = max(0.00002, base_no2 + urban_effect + np.random.normal(0, 0.00002))
            
            grid_cells.append({
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "value": round(no2, 8),
                "uncertainty": round(np.random.uniform(0.00001, 0.00003), 8),
            })
    
    return {
        "id": str(uuid4()),
        "source": "tropomi_no2",
        "data_type": "NO2",
        "observation_time": f"{date}T03:15:00Z",
        "fetch_time": datetime.utcnow().isoformat() + "Z",
        "bbox": bbox,
        "grid_cells": grid_cells,
        "grid_cell_count": len(grid_cells),
        "average_value": round(np.mean([c["value"] for c in grid_cells]), 8),
        "quality_flag": "good",
        "metadata": {
            "product": "L2__NO2___",
            "platform": "Sentinel-5P",
            "resolution": "7x3.5km",
            "processing_level": "OFFL",
        },
    }


def fetch_sample_data(
    city: str = "hcmc",
    days: int = 7,
    output_dir: str = None,
):
    """Fetch sample satellite data for multiple days and sources."""
    if city not in CITY_BBOXES:
        print(f"Unknown city: {city}. Available: {list(CITY_BBOXES.keys())}")
        sys.exit(1)
    
    city_info = CITY_BBOXES[city]
    bbox = {
        "north": city_info["north"],
        "south": city_info["south"],
        "east": city_info["east"],
        "west": city_info["west"],
    }
    
    # Set output directory
    if output_dir is None:
        output_dir = Path(__file__).parent / "sample_data" / city
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Fetching sample satellite data for {city_info['name']}")
    print(f"Bounding box: N{bbox['north']}, S{bbox['south']}, E{bbox['east']}, W{bbox['west']}")
    print(f"Date range: {days} days")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    all_data = {
        "city": city,
        "city_name": city_info["name"],
        "bbox": bbox,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sources": {},
    }
    
    # Generate data for each day
    dates = [datetime.utcnow() - timedelta(days=i) for i in range(days)]
    
    for source in ["cams_pm25", "modis_terra", "tropomi_no2"]:
        print(f"\nGenerating {source} data...")
        source_data = []
        
        for date in dates:
            date_str = date.strftime("%Y-%m-%d")
            
            if source == "cams_pm25":
                data = generate_mock_cams_data(bbox, date_str)
            elif source == "modis_terra":
                data = generate_mock_modis_data(bbox, date_str)
            elif source == "tropomi_no2":
                data = generate_mock_tropomi_data(bbox, date_str)
            else:
                continue
            
            source_data.append(data)
            print(f"  {date_str}: {data['grid_cell_count']} grid cells, "
                  f"avg={data['average_value']:.4f}")
        
        all_data["sources"][source] = source_data
    
    # Save combined data
    output_file = output_dir / "satellite_data.json"
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)
    
    print(f"\n✓ Saved combined data to: {output_file}")
    
    # Save individual source files
    for source, data in all_data["sources"].items():
        source_file = output_dir / f"{source}.json"
        with open(source_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✓ Saved {source} data to: {source_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for source, data in all_data["sources"].items():
        avg_values = [d["average_value"] for d in data]
        print(f"\n{source}:")
        print(f"  Total records: {len(data)}")
        print(f"  Average value: {np.mean(avg_values):.4f}")
        print(f"  Min value: {min(avg_values):.4f}")
        print(f"  Max value: {max(avg_values):.4f}")
    
    print(f"\n✓ Sample data generation complete!")
    print(f"  Total files created: {len(all_data['sources']) + 1}")
    
    return output_dir


def main():
    parser = argparse.ArgumentParser(
        description="Fetch sample satellite data for testing"
    )
    parser.add_argument(
        "--city",
        type=str,
        default="hcmc",
        choices=list(CITY_BBOXES.keys()),
        help="City to fetch data for",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days of data to generate",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: scripts/sample_data/<city>)",
    )
    
    args = parser.parse_args()
    
    output_dir = fetch_sample_data(
        city=args.city,
        days=args.days,
        output_dir=args.output,
    )
    
    print(f"\nTo use this data in tests, copy it to your test fixtures directory.")
    print(f"Example: cp -r {output_dir} services/remote-sensing-service/tests/fixtures/")


if __name__ == "__main__":
    main()
