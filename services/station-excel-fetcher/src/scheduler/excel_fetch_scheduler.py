"""APScheduler-based Excel fetch scheduler for Envisoft data.

Runs at :01 of every hour (01:01, 02:01, ... 23:01) to fetch data from Envisoft.
The fetched data is saved as Excel files in the configured output directory.
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
    """Parse a standard 5-field cron expression into an APScheduler CronTrigger."""
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Expected 5-field cron expression, got: {expression!r}")

    minute, hour, day, month, day_of_week = parts
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )


class ExcelFetchScheduler:
    """Manages periodic Envisoft Excel data fetch jobs.

    The scheduler runs at :01 of every hour to fetch the previous hour's data
    from the Envisoft API and save it as Excel files.
    """

    def __init__(self, fetch_callback=None):
        """Initialize scheduler.

        Args:
            fetch_callback: Async function to call for fetching data.
                           If None, uses the default Envisoft fetch logic.
        """
        self.fetch_callback = fetch_callback
        self.scheduler = AsyncIOScheduler()

    def start(self) -> None:
        """Register jobs and start the scheduler."""
        # Register the periodic fetch job
        self.scheduler.add_job(
            self._run_fetch,
            trigger=_parse_cron(config.FETCH_CRON_EXPRESSION),
            id="fetch_envisoft_excel",
            name="Fetch Envisoft data to Excel",
            replace_existing=True,
        )

        logger.info(
            f"Excel fetch job scheduled: {config.FETCH_CRON_EXPRESSION}"
        )

        self.scheduler.start()
        logger.info("ExcelFetchScheduler started")

    def stop(self) -> None:
        """Shut down the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("ExcelFetchScheduler stopped")

    async def _run_fetch(self) -> None:
        """Execute the scheduled fetch job."""
        logger.info("=" * 60)
        logger.info("Scheduler: Starting Envisoft Excel fetch")
        logger.info("=" * 60)

        try:
            # Determine date range
            now = datetime.utcnow()
            # Fetch yesterday and today (to catch any late data)
            from_date = (now - timedelta(days=config.FETCH_DAYS_BACK)).strftime("%Y-%m-%d")
            to_date = now.strftime("%Y-%m-%d")

            logger.info(f"Date range: {from_date} to {to_date}")

            # Use callback if provided, otherwise use default fetch
            if self.fetch_callback:
                await self.fetch_callback(
                    from_date=from_date,
                    to_date=to_date,
                    view_type=config.ENVISOFT_VIEW_TYPE,
                )
            else:
                await self._default_fetch(from_date, to_date)

            logger.info("Scheduler: Excel fetch completed successfully")

        except Exception:
            logger.exception("Scheduler: Excel fetch failed")

    async def _default_fetch(self, from_date: str, to_date: str) -> None:
        """Default fetch implementation using EnvisoftClient."""
        from .envisoft_client import EnvisoftClient

        async with EnvisoftClient() as client:
            # Fetch data for all stations
            records = await client.fetch_all_stations_data(
                from_date=from_date,
                to_date=to_date,
                station_type=config.ENVISOFT_STATION_TYPE,
                view_type=config.ENVISOFT_VIEW_TYPE,
            )

            if records:
                # Generate filename with timestamp
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"envisoft_{from_date}_{to_date}_{timestamp}.xlsx"

                # Save to Excel
                client.save_to_excel(records, filename, sheet_name="Air Quality Data")

                # Log to file
                log_file = config.log_dir / f"fetch_{timestamp}.log"
                log_file.write_text(
                    f"Fetched {len(records)} records\n"
                    f"Date range: {from_date} to {to_date}\n"
                    f"Output: {filename}\n"
                    f"Time: {datetime.utcnow().isoformat()}\n"
                )
            else:
                logger.warning("No data fetched")

    async def trigger_manual_fetch(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        view_type: str = "hour",
    ) -> dict:
        """Trigger an on-demand fetch.

        Args:
            from_date: Start date (defaults to FETCH_DAYS_BACK days ago)
            to_date: End date (defaults to today)
            view_type: Data averaging period

        Returns:
            Dict with status and details
        """
        now = datetime.utcnow()

        if from_date is None:
            from_date = (now - timedelta(days=config.FETCH_DAYS_BACK)).strftime("%Y-%m-%d")
        if to_date is None:
            to_date = now.strftime("%Y-%m-%d")

        logger.info(f"Manual fetch triggered: {from_date} to {to_date}")

        try:
            if self.fetch_callback:
                await self.fetch_callback(
                    from_date=from_date,
                    to_date=to_date,
                    view_type=view_type,
                )
            else:
                await self._default_fetch(from_date, to_date)

            return {"status": "ok", "from_date": from_date, "to_date": to_date}

        except Exception as e:
            logger.exception("Manual fetch failed")
            return {"status": "error", "message": str(e)}