"""MySQL repository for Envisoft hourly readings."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.dialects.mysql import insert

from .database import session_cm
from .models import EnvisoftHourlyReadingModel

logger = logging.getLogger(__name__)


class ReadingRepository:
    """Repository for bulk inserting and querying Envisoft hourly readings."""

    async def bulk_upsert(
        self,
        records: list[dict[str, Any]],
        excel_path: str | None = None,
    ) -> int:
        """Insert or update records using INSERT ... ON DUPLICATE KEY UPDATE.

        Args:
            records: List of dicts with station_id, measured_at, and field values.
            excel_path: Optional path to the Excel file source.

        Returns:
            Number of rows inserted/updated.
        """
        if not records:
            return 0

        now = datetime.utcnow()
        inserted = 0

        async with session_cm() as session:
            for record in records:
                # Merge excel_path into record
                row = {**record, "excel_path": excel_path, "fetched_at": now}

                # Remove None values to avoid SQL issues
                row = {k: v for k, v in row.items() if v is not None}

                stmt = insert(EnvisoftHourlyReadingModel).values(**row)
                stmt = stmt.on_duplicate_key_update(
                    {
                        k: stmt.inserted[k]
                        for k in row
                        if k not in ("station_id", "measured_at", "fetched_at")
                    }
                )
                await session.execute(stmt)
                inserted += 1

            await session.commit()

        logger.info(f"[DB] Bulk upserted {inserted} records")
        return inserted

    async def count_by_station(self, station_id: str) -> int:
        async with session_cm() as session:
            result = await session.execute(
                select(func.count(EnvisoftHourlyReadingModel.id)).where(
                    EnvisoftHourlyReadingModel.station_id == station_id
                )
            )
            return result.scalar_one()

    async def count_by_date_range(
        self,
        from_date: datetime,
        to_date: datetime,
    ) -> int:
        async with session_cm() as session:
            result = await session.execute(
                select(func.count(EnvisoftHourlyReadingModel.id)).where(
                    EnvisoftHourlyReadingModel.measured_at >= from_date,
                    EnvisoftHourlyReadingModel.measured_at <= to_date,
                )
            )
            return result.scalar_one()

    async def get_latest(self, station_id: str, limit: int = 24) -> list[EnvisoftHourlyReadingModel]:
        async with session_cm() as session:
            result = await session.execute(
                select(EnvisoftHourlyReadingModel)
                .where(EnvisoftHourlyReadingModel.station_id == station_id)
                .order_by(EnvisoftHourlyReadingModel.measured_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
