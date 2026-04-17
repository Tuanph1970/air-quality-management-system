"""MySQL repository for Envisoft hourly readings."""

from __future__ import annotations

import logging
from datetime import date as date_type, datetime, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.dialects.mysql import insert

from .database import session_cm
from .models import EnvisoftHourlyReadingModel, EnvisoftFetchLogModel

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

    # ─────────────────────────────────────────────────────────────────────────
    # Fetch log helpers (for retry / gap detection)
    # ─────────────────────────────────────────────────────────────────────────

    async def start_fetch_log(
        self,
        fetch_date: date_type,
        station_id: str,
        attempt: int,
    ) -> int:
        """Insert a pending fetch log entry, return its id."""
        async with session_cm() as session:
            stmt = insert(EnvisoftFetchLogModel).values(
                fetch_date=fetch_date,
                station_id=station_id,
                attempt=attempt,
                status="pending",
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.lastrowid

    async def complete_fetch_log(
        self,
        fetch_date: date_type,
        station_id: str,
        attempt: int,
        status: str,
        records_count: int | None = None,
        error_message: str | None = None,
        excel_path: str | None = None,
    ) -> None:
        """Update fetch log with final status."""
        async with session_cm() as session:
            # Find the latest attempt for this date+station
            result = await session.execute(
                select(EnvisoftFetchLogModel)
                .where(EnvisoftFetchLogModel.fetch_date == fetch_date)
                .where(EnvisoftFetchLogModel.station_id == station_id)
                .where(EnvisoftFetchLogModel.attempt == attempt)
            )
            log = result.scalar_one_or_none()
            if log:
                log.status = status
                log.records_count = records_count
                log.error_message = error_message
                log.finished_at = datetime.utcnow()
                log.excel_path = excel_path
                await session.commit()

    async def get_last_attempt(
        self,
        fetch_date: date_type,
        station_id: str,
    ) -> int | None:
        """Return the highest attempt number for a date+station, or None."""
        async with session_cm() as session:
            result = await session.execute(
                select(func.max(EnvisoftFetchLogModel.attempt))
                .where(EnvisoftFetchLogModel.fetch_date == fetch_date)
                .where(EnvisoftFetchLogModel.station_id == station_id)
            )
            return result.scalar_one_or_none()

    async def delete_fetch_logs(
        self,
        fetch_date: date_type,
        station_id: str,
    ) -> int:
        """Delete all fetch logs for a date+station (used when force-retrying)."""
        from sqlalchemy import delete as sql_delete

        async with session_cm() as session:
            result = await session.execute(
                sql_delete(EnvisoftFetchLogModel)
                .where(EnvisoftFetchLogModel.fetch_date == fetch_date)
                .where(EnvisoftFetchLogModel.station_id == station_id)
            )
            await session.commit()
            return result.rowcount

    async def get_fetch_log_summary(
        self,
        days_back: int = 7,
    ) -> list[dict]:
        """Return latest status per (date, station) for last N days."""
        from sqlalchemy import func, text

        async with session_cm() as session:
            today = datetime.utcnow().date()
            rows = []
            for days_ago in range(0, days_back):
                target_date = today - timedelta(days=days_ago)
                for sid in [
                    "32464751000956754854540602537",
                    "32464751000956754854540602541",
                    "32464751056296987075669257406",
                ]:
                    result = await session.execute(
                        select(EnvisoftFetchLogModel)
                        .where(EnvisoftFetchLogModel.fetch_date == target_date)
                        .where(EnvisoftFetchLogModel.station_id == sid)
                        .order_by(EnvisoftFetchLogModel.attempt.desc())
                        .limit(1)
                    )
                    log = result.scalar_one_or_none()
                    rows.append({
                        "fetch_date": target_date,
                        "station_id": sid,
                        "status": log.status if log else "never_run",
                        "attempt": log.attempt if log else 0,
                        "records_count": log.records_count if log else None,
                        "error_message": log.error_message if log else None,
                    })
            return rows

    async def get_missing_dates(
        self,
        days_back: int = 7,
    ) -> list[date_type]:
        """Return list of dates in the last N days that have no success for any station.

        Checks the 3 active stations.
        """
        active_stations = [
            "32464751000956754854540602537",
            "32464751000956754854540602541",
            "32464751056296987075669257406",
        ]

        missing: list[date_type] = []
        today = datetime.utcnow().date()

        async with session_cm() as session:
            for days_ago in range(1, days_back + 1):
                target_date = today - timedelta(days=days_ago)

                # Check if ALL active stations have a "success" entry for this date
                for sid in active_stations:
                    result = await session.execute(
                        select(func.count(EnvisoftFetchLogModel.id))
                        .where(EnvisoftFetchLogModel.fetch_date == target_date)
                        .where(EnvisoftFetchLogModel.station_id == sid)
                        .where(EnvisoftFetchLogModel.status == "success")
                    )
                    if result.scalar_one() == 0:
                        missing.append(target_date)
                        break  # one missing station is enough — skip remaining stations

        return missing
