"""ARQ worker configuration for background jobs."""

from arq import cron
from arq.connections import RedisSettings

from osrs_backend.db.database import connect_db, disconnect_db, get_db
from osrs_backend.tasks import (
    fetch_latest_prices,
    calculate_action_cost,
    fetch_item_list,
    fetch_backfill_prices,
)
from osrs_backend.utils.logging import setup_logging
from osrs_backend.config import get_settings

setup_logging()

# ARQ doesn't support */5 or */10 syntax
every_five_minutes = {0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}
every_ten_minutes = {0, 10, 20, 30, 40, 50}


async def startup(ctx):
    """Worker startup hook."""
    await connect_db()
    ctx["db"] = await get_db()
    return ctx


async def shutdown(ctx):
    """Worker shutdown hook."""
    await disconnect_db()
    return


def _get_redis_settings():
    """Get Redis settings from config."""
    settings = get_settings()
    return RedisSettings(host=settings.redis_host, port=settings.redis_port)


class WorkerSettings:
    """ARQ worker settings."""

    functions = [
        fetch_latest_prices,
        fetch_item_list,
        calculate_action_cost,
        fetch_backfill_prices,
    ]
    cron_jobs = [
        cron(fetch_latest_prices, minute=every_five_minutes),
        cron(fetch_item_list, minute=every_ten_minutes),
        cron(calculate_action_cost, minute=every_five_minutes),
        cron(
            fetch_backfill_prices,
            minute=every_five_minutes,
            unique=True,
        ),
    ]
    job_timeout = 600  # 10 minutes
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = _get_redis_settings()
