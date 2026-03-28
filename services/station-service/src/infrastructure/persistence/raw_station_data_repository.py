"""SQLAlchemy implementation of RawStationDataRepository."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, delete, and_, func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from .models import RawStationDataModel

logger = logging.getLogger(__name__)


class RawStationDataRepository:
    """Repository for raw station data from EnviSoft API.

    This repository handles storage and retrieval of raw 5-minute interval
    station data including all pollutant measurements, environmental data,
    and wind information.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: AsyncSession instance
        """
        self.session = session

    async def save_batch(
        self,
        station_id: str,
        records: List[Dict[str, Any]],
        source: str = "ENVISOFT_API",
    ) -> int:
        """Save a batch of raw data records.

        Uses MySQL INSERT ... ON DUPLICATE KEY UPDATE to handle duplicates
        gracefully (upsert behavior).

        Args:
            station_id: Station ID
            records: List of data records from EnviSoft API
            source: Data source identifier

        Returns:
            Number of records saved/updated
        """
        if not records:
            return 0

        saved_count = 0
        now = datetime.utcnow()

        for record in records:
            try:
                # Parse timestamp
                measured_at = self._parse_timestamp(
                    record.get("getTime") or record.get("time")
                )
                if not measured_at:
                    logger.warning(f"Skipping record with invalid timestamp: {record}")
                    continue

                # Build model data
                model_data = self._record_to_model_data(
                    station_id=station_id,
                    record=record,
                    measured_at=measured_at,
                    source=source,
                    now=now,
                )

                # Use upsert to handle duplicates
                stmt = mysql_insert(RawStationDataModel).values(**model_data)
                stmt = stmt.on_duplicate_key_update(**model_data)
                await self.session.execute(stmt)
                saved_count += 1

            except Exception as e:
                logger.error(f"Error saving record: {e}")
                continue

        await self.session.flush()
        logger.info(f"Saved {saved_count} raw data records for station {station_id}")
        return saved_count

    def _record_to_model_data(
        self,
        station_id: str,
        record: Dict[str, Any],
        measured_at: datetime,
        source: str,
        now: datetime,
    ) -> Dict[str, Any]:
        """Convert API record to model data.

        Args:
            station_id: Station ID
            record: Raw API record
            measured_at: Parsed measurement timestamp
            source: Data source
            now: Current timestamp

        Returns:
            Dictionary suitable for model creation
        """
        return {
            "station_id": station_id,
            "measured_at": measured_at,
            # Pollutants
            "no_value": self._to_float(record.get("no")),
            "o3_value": self._to_float(record.get("o3")),
            "co_value": self._to_float(record.get("co")),
            "no2_value": self._to_float(record.get("no2")),
            "nox_value": self._to_float(record.get("nox")),
            "so2_value": self._to_float(record.get("so2")),
            "pm10_value": self._to_float(record.get("pm10")),
            "pm25_value": self._to_float(record.get("pm25")),
            # Environmental
            "temperature": self._to_float(record.get("temperature")),
            "humidity": self._to_float(record.get("humidity")),
            "pressure": self._to_float(record.get("pressure")),
            # Wind
            "wind_speed": self._to_float(record.get("windspeed") or record.get("wind_speed")),
            "wind_direction": self._to_float(
                record.get("winddirection") or record.get("wind_direction")
            ),
            # Additional
            "aqi": self._to_float(record.get("aqi")),
            "aqi_category": record.get("aqi_category") or record.get("category"),
            # Metadata
            "source": source,
            "fetched_at": now,
            "raw_data": record,
        }

    def _to_float(self, value: Any) -> Optional[float]:
        """Convert value to float safely.

        Args:
            value: Value to convert

        Returns:
            Float value or None
        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse timestamp from various formats.

        Args:
            value: Timestamp value (string, datetime, etc.)

        Returns:
            Parsed datetime or None
        """
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(value)

        if isinstance(value, str):
            # ISO format with various possible formats
            value = value.replace("Z", "+00:00")
            for fmt in [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
            ]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

        return None

    async def get_by_station(
        self,
        station_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 1000,
    ) -> List[RawStationDataModel]:
        """Get raw data for a station.

        Args:
            station_id: Station ID
            start_time: Optional start time filter
            end_time: Optional end time filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of raw data records
        """
        query = select(RawStationDataModel).where(
            RawStationDataModel.station_id == station_id
        )

        if start_time:
            query = query.where(RawStationDataModel.measured_at >= start_time)
        if end_time:
            query = query.where(RawStationDataModel.measured_at <= end_time)

        query = query.order_by(RawStationDataModel.measured_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_station(
        self,
        station_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Count raw data records for a station.

        Args:
            station_id: Station ID
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Count of matching records
        """
        query = select(func.count(RawStationDataModel.id)).where(
            RawStationDataModel.station_id == station_id
        )

        if start_time:
            query = query.where(RawStationDataModel.measured_at >= start_time)
        if end_time:
            query = query.where(RawStationDataModel.measured_at <= end_time)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def delete_old_records(self, older_than: datetime) -> int:
        """Delete raw data older than specified timestamp.

        Args:
            older_than: Delete records older than this timestamp

        Returns:
            Number of records deleted
        """
        stmt = delete(RawStationDataModel).where(
            RawStationDataModel.measured_at < older_than
        )

        result = await self.session.execute(stmt)
        deleted = result.rowcount
        logger.info(f"Deleted {deleted} raw data records older than {older_than}")
        return deleted

    async def get_latest_fetch_time(self, station_id: str) -> Optional[datetime]:
        """Get the latest data fetch time for a station.

        Args:
            station_id: Station ID

        Returns:
            Latest fetched_at timestamp or None
        """
        query = (
            select(func.max(RawStationDataModel.fetched_at))
            .where(RawStationDataModel.station_id == station_id)
        )

        result = await self.session.execute(query)
        return result.scalar() or None

    async def get_measurement_range(
        self, station_id: str
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get the measurement time range for a station.

        Args:
            station_id: Station ID

        Returns:
            Tuple of (earliest_measured_at, latest_measured_at)
        """
        min_query = (
            select(func.min(RawStationDataModel.measured_at))
            .where(RawStationDataModel.station_id == station_id)
        )
        max_query = (
            select(func.max(RawStationDataModel.measured_at))
            .where(RawStationDataModel.station_id == station_id)
        )

        min_result = await self.session.execute(min_query)
        max_result = await self.session.execute(max_query)

        return min_result.scalar() or None, max_result.scalar() or None
