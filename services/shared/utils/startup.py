"""Startup utilities for resilient service initialization.

Provides retry logic for database and message broker connections so
services self-heal on slow / resource-constrained hardware without
requiring operator intervention.
"""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


async def init_db_with_retry(
    engine,
    metadata,
    max_retries: int = 15,
    initial_delay: float = 2.0,
    max_delay: float = 30.0,
) -> None:
    """Create DB tables with exponential-backoff retry.

    On weak hardware MySQL may accept the healthcheck ping but not yet be
    fully ready to serve application queries.  This function retries the
    ``CREATE TABLE IF NOT EXISTS`` call so the service recovers on its own
    instead of crashing and waiting for Docker to restart it.

    Args:
        engine: SQLAlchemy ``AsyncEngine`` to use.
        metadata: ``MetaData`` object (e.g. ``Base.metadata``).
        max_retries: Maximum number of connection attempts before giving up.
        initial_delay: Seconds to wait before the second attempt.
        max_delay: Maximum seconds to wait between attempts (caps backoff).
    """
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(metadata.create_all)
            logger.info("Database tables verified/created (attempt %d)", attempt)
            return
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt == max_retries:
                break
            wait = min(initial_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                "Database not ready (attempt %d/%d): %s — retrying in %.0fs …",
                attempt,
                max_retries,
                exc,
                wait,
            )
            await asyncio.sleep(wait)

    logger.error(
        "Database initialization failed after %d attempts: %s",
        max_retries,
        last_exc,
    )
    raise RuntimeError(
        f"Could not initialize database after {max_retries} attempts"
    ) from last_exc
