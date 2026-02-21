"""Scheduler main entry point."""

import logging

import uvicorn
from fastapi import FastAPI

from common.utils.config import get_settings
from common.utils.database import init_db
from scheduler.api_gateway import create_app
from scheduler.dispatcher import dispatcher

settings = get_settings()
logging.basicConfig(
    level=logging.DEBUG if settings.server_debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app: FastAPI = create_app()


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize on startup."""
    logger.info("Starting VulnScan Engine Scheduler...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    # Connect to RabbitMQ (optional)
    try:
        await dispatcher.connect()
        logger.info("Connected to RabbitMQ")
    except Exception as e:
        logger.warning(f"RabbitMQ connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down VulnScan Engine Scheduler...")
    await dispatcher.disconnect()


def main() -> None:
    """Run the scheduler server."""
    uvicorn.run(
        "scheduler.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_debug,
    )


if __name__ == "__main__":
    main()
