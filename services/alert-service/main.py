"""Alert Service — Entry Point.

Starts the FastAPI application via Uvicorn.  The lifespan hook in
``src.interfaces.api.routes`` handles database, publisher, and consumer
initialisation.
"""
import logging
import sys

import uvicorn


def main() -> None:
    """Configure logging and start the ASGI server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    uvicorn.run(
        "src.interfaces.api.routes:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
    )


if __name__ == "__main__":
    main()
