"""APScheduler-based daily fetch scheduler for Envisoft data.

Runs at 00:01 AM daily to fetch the previous full day's data from Envisoft
for 3 target stations (556 Nguyễn Văn Cừ, ĐHBK, Công viên Nhân Chính).

Features:
  - Retry: each station gets MAX_RETRIES attempts if it fails
  - Catch-up: on every run, also checks last 7 days for missing data and re-fetches
  - Fetch logs: every attempt is recorded in envisoft_fetch_logs table
  - Manual endpoint: POST /retry to manually trigger catch-up for a specific date

Flow (per station):
  1. Log attempt start (status=pending)
  2. Launch Playwright → iframe login → select station → set date → export Excel
  3. Parse Excel → bulk upsert to MySQL
  4. Update log (status=success/failed, records_count, error_message)
  5. If failed and attempts < MAX_RETRIES → retry after 60s backoff
"""

from __future__ import annotations

import logging
import time
from datetime import date as date_type, datetime, timedelta
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import config

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 60


def _parse_cron(expression: str) -> CronTrigger:
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Expected 5-field cron, got: {expression!r}")

    minute, hour, day, month, day_of_week = parts
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )


class ExcelFetchScheduler:
    """Daily scheduler that fetches Envisoft data → Excel → MySQL with retry + catch-up."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self.scheduler.add_job(
            self._run_fetch,
            trigger=_parse_cron(config.FETCH_CRON_EXPRESSION),
            id="fetch_envisoft_daily",
            name="Fetch Envisoft daily Excel + MySQL",
            replace_existing=True,
        )
        logger.info(
            f"Daily fetch scheduled: cron={config.FETCH_CRON_EXPRESSION} "
            f"(fetches previous day + catches up missing days in last 7 days)"
        )
        self.scheduler.start()
        logger.info("ExcelFetchScheduler started")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("ExcelFetchScheduler stopped")

    # ─────────────────────────────────────────────────────────────────────────
    # Core fetch logic (also called by /fetch and /retry endpoints)
    # ─────────────────────────────────────────────────────────────────────────

    async def fetch_date(
        self,
        fetch_date: date_type,
        stations: list[dict],
        repo,
        force: bool = False,
    ) -> dict[str, int]:
        """Fetch data for one date across all stations, with retry per station.

        Args:
            fetch_date: The date to fetch data for
            stations: config.TARGET_STATIONS list
            repo: ReadingRepository instance
            force: If True, re-fetch even if success log exists for this date

        Returns:
            Dict mapping station_id → records fetched (0 if failed)
        """
        results: dict[str, int] = {}

        for station in stations:
            station_id = station["station_id"]
            station_name = station["name"]

            # Determine attempt number
            if force:
                # Force: reset attempt to 1 (overwrite existing logs)
                attempt = 1
                await repo.delete_fetch_logs(fetch_date, station_id)
            else:
                last_attempt = await repo.get_last_attempt(fetch_date, station_id)
                attempt = (last_attempt or 0) + 1

            if attempt > MAX_RETRIES:
                logger.warning(
                    f"[SCHEDULER] {station_name}: max retries ({MAX_RETRIES}) exceeded, skipping"
                )
                results[station_id] = 0
                continue

            # Log start
            await repo.start_fetch_log(fetch_date, station_id, attempt)
            started_at = datetime.utcnow()
            logger.info(
                f"[SCHEDULER] {station_name}: attempt {attempt}/{MAX_RETRIES} "
                f"for {fetch_date}, started at {started_at:%H:%M:%S}"
            )

            try:
                # Import here to avoid circular dependency at module load time
                from ..fetcher.envisoft_client import EnvisoftClient

                async with EnvisoftClient() as client:
                    records = await client.export_station_data_full(
                        station_id=station_id,
                        station_name=station_name,
                        station_index=0,  # we always pre-select province once
                        from_date=fetch_date.strftime("%Y-%m-%d"),
                        to_date=fetch_date.strftime("%Y-%m-%d"),
                    )

                if not records:
                    logger.warning(
                        f"[SCHEDULER] {station_name}: 0 records exported for {fetch_date}"
                    )
                    await repo.complete_fetch_log(
                        fetch_date=fetch_date,
                        station_id=station_id,
                        attempt=attempt,
                        status="failed",
                        records_count=0,
                        error_message="No records exported (Envisoft returned empty data or export timed out)",
                    )
                    # No data → treat as failure → retry
                    if attempt < MAX_RETRIES:
                        logger.info(f"[SCHEDULER] {station_name}: will retry in {RETRY_BACKOFF_SECONDS}s")
                        await self._sleep(RETRY_BACKOFF_SECONDS)
                        # Increment attempt and log it
                        await repo.start_fetch_log(fetch_date, station_id, attempt + 1)
                        # Re-fetch inside same station loop (recursive retry)
                        # Use force=True to prevent infinite loop
                        inner_records = await self._fetch_single_station(
                            fetch_date, station_id, station_name, repo, force=True
                        )
                        results[station_id] = inner_records
                    else:
                        results[station_id] = 0
                else:
                    # Upsert to MySQL
                    inserted = await repo.bulk_upsert(records=records)
                    await repo.complete_fetch_log(
                        fetch_date=fetch_date,
                        station_id=station_id,
                        attempt=attempt,
                        status="success",
                        records_count=inserted,
                    )
                    logger.info(
                        f"[SCHEDULER] {station_name}: ✓ {inserted} records upserted "
                        f"(attempt {attempt})"
                    )
                    results[station_id] = inserted

            except Exception as exc:
                logger.exception(f"[SCHEDULER] {station_name}: FAILED on attempt {attempt}")
                await repo.complete_fetch_log(
                    fetch_date=fetch_date,
                    station_id=station_id,
                    attempt=attempt,
                    status="failed",
                    records_count=0,
                    error_message=str(exc),
                )
                if attempt < MAX_RETRIES:
                    logger.info(f"[SCHEDULER] {station_name}: will retry in {RETRY_BACKOFF_SECONDS}s")
                    await self._sleep(RETRY_BACKOFF_SECONDS)
                    # Retry: call _fetch_single_station for the same station
                    retried = await self._fetch_single_station(
                        fetch_date, station_id, station_name, repo, force=False
                    )
                    results[station_id] = retried
                else:
                    results[station_id] = 0

        return results

    async def _fetch_single_station(
        self,
        fetch_date: date_type,
        station_id: str,
        station_name: str,
        repo,
        force: bool,
    ) -> int:
        """Fetch a single station with retry, return records count."""
        from ..fetcher.envisoft_client import EnvisoftClient

        attempt = await repo.get_last_attempt(fetch_date, station_id) or 0
        next_attempt = attempt + 1

        if next_attempt > MAX_RETRIES:
            return 0

        await repo.start_fetch_log(fetch_date, station_id, next_attempt)

        try:
            async with EnvisoftClient() as client:
                records = await client.export_station_data_full(
                    station_id=station_id,
                    station_name=station_name,
                    station_index=0,
                    from_date=fetch_date.strftime("%Y-%m-%d"),
                    to_date=fetch_date.strftime("%Y-%m-%d"),
                )

            if not records:
                await repo.complete_fetch_log(
                    fetch_date, station_id, next_attempt,
                    status="failed",
                    records_count=0,
                    error_message="No records exported",
                )
                # Retry if we have attempts left
                if next_attempt < MAX_RETRIES:
                    await self._sleep(RETRY_BACKOFF_SECONDS)
                    return await self._fetch_single_station(
                        fetch_date, station_id, station_name, repo, force=False
                    )
                return 0

            inserted = await repo.bulk_upsert(records=records)
            await repo.complete_fetch_log(
                fetch_date, station_id, next_attempt,
                status="success",
                records_count=inserted,
            )
            return inserted

        except Exception as exc:
            logger.exception(f"[SCHEDULER] {station_name}: retry attempt {next_attempt} FAILED")
            await repo.complete_fetch_log(
                fetch_date, station_id, next_attempt,
                status="failed",
                records_count=0,
                error_message=str(exc),
            )
            if next_attempt < MAX_RETRIES:
                await self._sleep(RETRY_BACKOFF_SECONDS)
                return await self._fetch_single_station(
                    fetch_date, station_id, station_name, repo, force=False
                )
            return 0

    async def _sleep(self, seconds: int) -> None:
        """Async sleep wrapper for testability."""
        import asyncio
        await asyncio.sleep(seconds)

    # ─────────────────────────────────────────────────────────────────────────
    # Scheduled run
    # ─────────────────────────────────────────────────────────────────────────

    async def _run_fetch(self) -> None:
        """Execute the scheduled daily fetch: yesterday + catch-up missing days."""
        logger.info("=" * 60)
        logger.info("Scheduler: Starting daily Envisoft fetch")
        logger.info("=" * 60)

        try:
            from ..infrastructure.persistence.reading_repository import ReadingRepository

            repo = ReadingRepository()
            stations = config.TARGET_STATIONS

            # 1. Check missing dates from last 7 days
            missing_dates = await repo.get_missing_dates(days_back=7)
            if missing_dates:
                logger.info(
                    f"[SCHEDULER] Catch-up: found {len(missing_dates)} missing date(s): "
                    f"{[str(d) for d in missing_dates]}"
                )
            else:
                logger.info("[SCHEDULER] No missing dates in last 7 days")

            # 2. Yesterday (primary scheduled run)
            yesterday = datetime.utcnow().date() - timedelta(days=1)
            dates_to_fetch = [yesterday] + missing_dates

            total_all = 0
            for fetch_d in dates_to_fetch:
                logger.info(f"[SCHEDULER] Fetching date: {fetch_d}")
                results = await self.fetch_date(fetch_d, stations, repo, force=False)
                total = sum(results.values())
                total_all += total
                logger.info(
                    f"[SCHEDULER] Date {fetch_d}: "
                    f"{total} total records across {len(stations)} stations"
                )

            logger.info(f"[SCHEDULER] All done: {total_all} records fetched this run")

        except Exception:
            logger.exception("Scheduler: Daily fetch FAILED")

    # ─────────────────────────────────────────────────────────────────────────
    # Manual / API triggers
    # ─────────────────────────────────────────────────────────────────────────

    async def trigger_manual_fetch(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        force: bool = False,
    ) -> dict:
        """Trigger an on-demand fetch (POST /fetch endpoint).

        Args:
            from_date: Start date YYYY-MM-DD (defaults to yesterday)
            to_date: End date YYYY-MM-DD (defaults to yesterday)
            force: If True, re-fetch even if success log exists

        Returns:
            Dict with status and details.
        """
        from ..infrastructure.persistence.reading_repository import ReadingRepository

        yesterday = (datetime.utcnow().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        if from_date is None:
            from_date = yesterday
        if to_date is None:
            to_date = yesterday

        logger.info(f"[MANUAL] Fetch triggered: {from_date} → {to_date}, force={force}")

        try:
            repo = ReadingRepository()
            stations = config.TARGET_STATIONS

            from_d = date_type.fromisoformat(from_date)
            to_d = date_type.fromisoformat(to_date)

            grand_total = 0
            all_results: dict[str, dict] = {}

            # Fetch each date in range
            current = from_d
            while current <= to_d:
                results = await self.fetch_date(current, stations, repo, force=force)
                total = sum(results.values())
                all_results[str(current)] = results
                grand_total += total
                current += timedelta(days=1)

            return {
                "status": "ok",
                "from_date": from_date,
                "to_date": to_date,
                "total_records": grand_total,
                "per_date": all_results,
            }
        except Exception as exc:
            logger.exception("[MANUAL] Fetch failed")
            return {"status": "error", "message": str(exc)}

    async def trigger_retry(self, fetch_date: Optional[str] = None) -> dict:
        """Retry fetching a specific date (POST /retry endpoint).

        Args:
            fetch_date: YYYY-MM-DD date to re-fetch (defaults to yesterday)

        Returns:
            Dict with status and results.
        """
        from ..infrastructure.persistence.reading_repository import ReadingRepository

        if fetch_date is None:
            fetch_date = (datetime.utcnow().date() - timedelta(days=1)).strftime("%Y-%m-%d")

        logger.info(f"[RETRY] Retrying date: {fetch_date}")

        try:
            repo = ReadingRepository()
            stations = config.TARGET_STATIONS
            fd = date_type.fromisoformat(fetch_date)

            results = await self.fetch_date(fd, stations, repo, force=True)
            total = sum(results.values())

            return {
                "status": "ok",
                "fetch_date": fetch_date,
                "results": results,
                "total_records": total,
            }
        except Exception as exc:
            logger.exception("[RETRY] Retry failed")
            return {"status": "error", "message": str(exc)}