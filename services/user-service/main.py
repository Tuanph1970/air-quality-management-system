"""User Service — Entry Point.

Starts the FastAPI application via Uvicorn. The lifespan hook in
``src.interfaces.api.routes`` handles database initialization.

Usage::

    # Development (with hot-reload)
    python main.py

    # Production (via Docker CMD)
    uvicorn src.interfaces.api.routes:app --host 0.0.0.0 --port 8005
"""
from __future__ import annotations

import logging
import sys

import uvicorn

from src.config import settings


def _configure_logging() -> None:
    """Set up root logger with a consistent format."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def main() -> None:
    """Run the user service."""
    _configure_logging()

    logger = logging.getLogger(__name__)
    logger.info(
        "Starting %s on port %d (log_level=%s)",
        settings.SERVICE_NAME,
        settings.SERVICE_PORT,
        settings.LOG_LEVEL,
    )

    uvicorn.run(
        "src.interfaces.api.routes:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
