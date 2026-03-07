"""Station Service - Application entry point.

Starts the uvicorn server for the FastAPI application.

Usage:
    # Development (with hot-reload)
    python main.py

    # Production
    uvicorn src.interfaces.api.routes:app --host 0.0.0.0 --port 8007
"""
from __future__ import annotations

import logging
import sys

import uvicorn

from src.config import settings


def _configure_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def main() -> None:
    """Run the station service."""
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
