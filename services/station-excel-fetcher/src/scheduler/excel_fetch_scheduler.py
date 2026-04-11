"""APScheduler-based daily fetch scheduler for Envisoft data.

Runs at 00:01 AM daily to fetch the previous full day's hourly data
from Envisoft for 5 target stations.

Flow:
  1. Launch Playwright → iframe login → capture JWT + tenantToken
  2. Fetch hourly data for all 5 stations
  3. Save to Excel (kept on disk for data correction)
  4. Bulk upsert into MySQL (upsert = INSERT ON DUPLICATE KEY UPDATE)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import config

logger = logging.getLogger(__name__)


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
    """Daily scheduler that fetches Envisoft data → Excel → MySQL."""

    def __init__(self, fetch_callback=None):
        self.fetch_callback = fetch_callback
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
            f"Daily fetch scheduled: {config.FETCH_CRON_EXPRESSION} "
            f"(runs at {config.FETCH_CRON_EXPRESSION} → fetches previous day)"
        )
        self.scheduler.start()
        logger.info("ExcelFetchScheduler started")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("ExcelFetchScheduler stopped")

    async def _run_fetch(self) -> None:
        """Execute the daily scheduled fetch."""
        logger.info("=" * 60)
        logger.info("Scheduler: Starting daily Envisoft fetch")
        logger.info("=" * 60)

        try:
            await self._default_fetch()
            logger.info("Scheduler: Daily fetch completed successfully")
        except Exception:
            logger.exception("Scheduler: Daily fetch FAILED")

    async def _default_fetch(self) -> None:
        """Fetch → Excel downloads → parse → MySQL pipeline."""
        from ..fetcher.envisoft_client import EnvisoftClient
        from ..infrastructure.persistence.reading_repository import ReadingRepository

        # ── Determine date range ──────────────────────────────────────────
        # Previous full day (00:00:00 → 23:59:59)
        today = datetime.utcnow().date()
        from_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        to_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")

        logger.info(f"[SCHEDULER] Exporting: {from_date}")
        logger.info(f"[SCHEDULER] Stations: {len(config.TARGET_STATIONS)}")

        # ── Fetch data via Playwright Excel export ──────────────────────────
        async with EnvisoftClient() as client:
            records = await client.export_all_stations_data(
                from_date=from_date,
                to_date=to_date,
            )

            if not records:
                logger.warning("[SCHEDULER] No records fetched — skipping save")
                return

            # ── Save to MySQL ────────────────────────────────────────────────
            repo = ReadingRepository()
            inserted = await repo.bulk_upsert(records=records)
            logger.info(f"[SCHEDULER] MySQL upserted: {inserted} rows")

            # ── Log summary ─────────────────────────────────────────────
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            log_file = config.log_dir / f"fetch_{timestamp}.log"
            log_file.write_text(
                f"Date: {from_date}\n"
                f"Stations: {len(config.TARGET_STATIONS)}\n"
                f"Records fetched: {len(records)}\n"
                f"MySQL upserted: {inserted}\n"
                f"Timestamp: {datetime.utcnow().isoformat()}\n"
            )
            logger.info(f"[SCHEDULER] Log: {log_file}")

    async def trigger_manual_fetch(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> dict:
        """Trigger an on-demand fetch.

        Args:
            from_date: Start date YYYY-MM-DD (defaults to yesterday)
            to_date: End date YYYY-MM-DD (defaults to yesterday)

        Returns:
            Dict with status and details.
        """
        yesterday = (datetime.utcnow().date() - timedelta(days=1)).strftime("%Y-%m-%d")

        if from_date is None:
            from_date = yesterday
        if to_date is None:
            to_date = yesterday

        logger.info(f"[MANUAL] Fetch triggered: {from_date} → {to_date}")

        try:
            await self._default_fetch()
            return {
                "status": "ok",
                "from_date": from_date,
                "to_date": to_date,
            }
        except Exception as exc:
            logger.exception("[MANUAL] Fetch failed")
            return {"status": "error", "message": str(exc)}
