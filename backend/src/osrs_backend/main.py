"""Unified entry point for the OSRS backend.

This module starts both the FastAPI HTTP server and the TCP inference server
in a single process using asyncio.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from arq import create_pool
from arq.connections import RedisSettings
import uvicorn

from osrs_backend.api.routers import router
from osrs_backend.db.database import connect_db, disconnect_db
from osrs_backend.tcp.server import create_tcp_server
from osrs_backend.utils.logging import setup_logging
from osrs_backend.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def unified_lifespan(app: FastAPI):
    """Lifespan context manager that starts both HTTP and TCP servers."""
    settings = get_settings()

    # Startup
    logger.info("Starting OSRS Backend...")

    # Connect to database (optional - server can run without it)
    try:
        await connect_db()
        app.state.db_connected = True
        logger.info("Database connected")
    except Exception as e:
        app.state.db_connected = False
        logger.warning(f"Database connection failed (database endpoints disabled): {e}")

    # Connect to Redis for ARQ
    try:
        app.state.arq_pool = await create_pool(
            RedisSettings(host=settings.redis_host, port=settings.redis_port)
        )
        logger.info(f"Redis connected at {settings.redis_host}:{settings.redis_port}")
    except Exception as e:
        logger.warning(f"Redis connection failed (background jobs disabled): {e}")
        app.state.arq_pool = None

    # Start TCP inference server
    tcp_server = None
    try:
        tcp_server = await create_tcp_server(
            host=settings.tcp_host,
            port=settings.tcp_port,
            models_dir=settings.models_dir,
            pool_size=settings.ml_processor_pool_size,
            processor_type=settings.ml_processor_type,
            device=settings.ml_device,
        )
        app.state.tcp_server = tcp_server
        logger.info(f"TCP inference server started on {settings.tcp_host}:{settings.tcp_port}")
    except Exception as e:
        logger.warning(f"TCP inference server failed to start: {e}")
        app.state.tcp_server = None

    logger.info("OSRS Backend started successfully")
    logger.info(f"HTTP API: http://{settings.http_host}:{settings.http_port}")
    if tcp_server:
        logger.info(f"TCP Inference: {settings.tcp_host}:{settings.tcp_port}")

    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down OSRS Backend...")

        if tcp_server:
            await tcp_server.stop()
            logger.info("TCP inference server stopped")

        if app.state.arq_pool:
            await app.state.arq_pool.close()
            logger.info("Redis connection closed")

        if getattr(app.state, 'db_connected', False):
            await disconnect_db()
            logger.info("Database disconnected")
        logger.info("OSRS Backend shutdown complete")


def create_unified_app() -> FastAPI:
    """Create the unified FastAPI application."""
    setup_logging()

    app = FastAPI(
        title="OSRS Backend",
        description="Unified HTTP API and ML inference server for OSRS automation",
        version="1.0.0",
        lifespan=unified_lifespan,
    )
    app.include_router(router)

    @app.get("/")
    async def root():
        return {
            "message": "Welcome to OSRS Backend",
            "status": "ok",
            "docs": "/docs",
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


# Create the app instance
app = create_unified_app()


def run_server(
    http_only: bool = False,
    tcp_only: bool = False,
    http_host: str | None = None,
    http_port: int | None = None,
):
    """Run the unified server."""
    settings = get_settings()
    host = http_host or settings.http_host
    port = http_port or settings.http_port

    if tcp_only:
        # Run only TCP server
        asyncio.run(_run_tcp_only())
    else:
        # Run HTTP server (which also starts TCP via lifespan if not http_only)
        uvicorn.run(
            "osrs_backend.main:app",
            host=host,
            port=port,
            reload=False,
        )


async def _run_tcp_only():
    """Run only the TCP inference server."""
    setup_logging()
    settings = get_settings()

    logger.info("Starting TCP-only mode...")
    tcp_server = await create_tcp_server(
        host=settings.tcp_host,
        port=settings.tcp_port,
        models_dir=settings.models_dir,
        pool_size=settings.ml_processor_pool_size,
        processor_type=settings.ml_processor_type,
        device=settings.ml_device,
    )

    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await tcp_server.stop()


if __name__ == "__main__":
    run_server()
