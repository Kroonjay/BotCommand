"""FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from http import HTTPStatus
from os import getenv

from arq import create_pool
from arq.connections import RedisSettings

from osrs_backend.db.database import connect_db, disconnect_db
from osrs_backend.api.routers import router
from osrs_backend.utils.logging import setup_logging
from osrs_backend.config import get_settings


def create_app(lifespan=None) -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()

    if lifespan is None:
        lifespan = default_lifespan

    app = FastAPI(
        title="OSRS Backend",
        description="Unified HTTP API and ML inference server for OSRS automation",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(router)

    @app.get("/")
    async def get_index():
        return {"message": "Welcome to OSRS Backend API", "status": "ok"}

    return app


@asynccontextmanager
async def default_lifespan(app: FastAPI):
    """Default lifespan context manager for the FastAPI app."""
    settings = get_settings()

    # Startup
    await connect_db()
    app.state.arq_pool = await create_pool(
        RedisSettings(host=settings.redis_host, port=settings.redis_port)
    )

    try:
        yield
    finally:
        # Shutdown
        await app.state.arq_pool.close()
        await disconnect_db()


# Create default app instance
app = create_app()
