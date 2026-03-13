"""Raw data storage for PurpleAir sensor readings."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RawDataStorage:
    """Store raw PurpleAir API responses to disk.
    
    Organizes data in folder structure:
    raw_data/
    └── {sensor_id}/
        └── {YYYY-MM}/
            └── {YYYY-MM-DD}_{sensor_id}.json
    """
    
    def __init__(self, base_dir: str = "./data/purpleair/raw"):
        """Initialize raw data storage.
        
        Args:
            base_dir: Base directory for raw data storage
        """
        self.base_dir = Path(base_dir)
        self._initialized = False
    
    def _ensure_dirs(self) -> None:
        """Ensure base directory exists."""
        if not self._initialized:
            try:
                self.base_dir.mkdir(parents=True, exist_ok=True)
                self._initialized = True
                logger.info(f"Raw data storage initialized at {self.base_dir}")
            except OSError as e:
                logger.error(f"Failed to create raw data directory: {e}")
                raise
    
    def _get_storage_path(self, sensor_id: int, timestamp: Optional[datetime] = None) -> Path:
        """Get storage path for a sensor reading.
        
        Args:
            sensor_id: PurpleAir sensor ID
            timestamp: Reading timestamp (defaults to now)
            
        Returns:
            Full path to storage file
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Create folder structure: {sensor_id}/{YYYY-MM}/
        month_folder = timestamp.strftime("%Y-%m")
        sensor_dir = self.base_dir / str(sensor_id) / month_folder
        sensor_dir.mkdir(parents=True, exist_ok=True)
        
        # Filename: {YYYY-MM-DD}_{sensor_id}.json
        filename = f"{timestamp.strftime('%Y-%m-%d')}_{sensor_id}.json"
        return sensor_dir / filename
    
    def save_reading(
        self,
        sensor_id: int,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> Path:
        """Save a raw sensor reading to disk.
        
        Args:
            sensor_id: PurpleAir sensor ID
            data: Raw API response data
            timestamp: Reading timestamp (defaults to now)
            
        Returns:
            Path to saved file
        """
        self._ensure_dirs()
        
        file_path = self._get_storage_path(sensor_id, timestamp)
        
        # Prepare data with metadata
        storage_data = {
            "sensor_id": sensor_id,
            "stored_at": datetime.utcnow().isoformat(),
            "reading_timestamp": timestamp.isoformat() if timestamp else None,
            "data": data,
        }
        
        # Append to file if it exists, otherwise create new
        existing_data = []
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to read existing file {file_path}: {e}")
                existing_data = []
        
        # Add new reading
        existing_data.append(storage_data)
        
        # Write back
        try:
            with open(file_path, "w") as f:
                json.dump(existing_data, f, indent=2)
            logger.debug(f"Saved raw data for sensor {sensor_id} to {file_path}")
            return file_path
        except IOError as e:
            logger.error(f"Failed to save raw data: {e}")
            raise
    
    def get_latest_reading(self, sensor_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest stored reading for a sensor.
        
        Args:
            sensor_id: PurpleAir sensor ID
            
        Returns:
            Latest reading data or None if not found
        """
        self._ensure_dirs()
        
        # Find most recent month folder
        sensor_dir = self.base_dir / str(sensor_id)
        if not sensor_dir.exists():
            return None
        
        month_folders = sorted([d for d in sensor_dir.iterdir() if d.is_dir()], reverse=True)
        if not month_folders:
            return None
        
        # Find most recent file in most recent month
        for month_folder in month_folders:
            files = sorted(
                [f for f in month_folder.iterdir() if f.is_file() and f.suffix == ".json"],
                reverse=True,
            )
            if files:
                try:
                    with open(files[0], "r") as f:
                        data = json.load(f)
                        if isinstance(data, list) and data:
                            return data[-1]  # Last reading in file
                        elif isinstance(data, dict):
                            return data
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to read {files[0]}: {e}")
                    continue
        
        return None
    
    def cleanup_old_data(self, retention_days: int = 90) -> int:
        """Remove raw data older than specified retention period.
        
        Args:
            retention_days: Number of days to retain data
            
        Returns:
            Number of files deleted
        """
        from datetime import timedelta
        
        self._ensure_dirs()
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        deleted_count = 0
        
        for sensor_dir in self.base_dir.iterdir():
            if not sensor_dir.is_dir():
                continue
            
            for month_folder in sensor_dir.iterdir():
                if not month_folder.is_dir():
                    continue
                
                for file_path in month_folder.iterdir():
                    if not file_path.is_file():
                        continue
                    
                    # Parse date from filename
                    try:
                        date_str = file_path.stem.split("_")[0]
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        if file_date < cutoff:
                            file_path.unlink()
                            deleted_count += 1
                            logger.debug(f"Deleted old file: {file_path}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse date from {file_path}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old raw data files")
        
        return deleted_count
