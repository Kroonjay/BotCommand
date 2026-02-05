"""Fetch and backfill windowed price data from OSRS Wiki API."""

from typing import Dict, List
from aiohttp import ClientSession
from datetime import datetime, timezone, timedelta
from prisma.enums import PriceWindow

from osrs_backend.models.item_price import WindowItemPriceCreate
from osrs_backend.config import get_settings


async def fetch_window(
    window: PriceWindow = PriceWindow.FIVE_MINUTES, start_time: datetime = None
) -> List[WindowItemPriceCreate]:
    """Fetch windowed time series (/5m, /1h, /24h) from OSRS Wiki API."""
    settings = get_settings()
    headers = {"User-Agent": settings.wiki_api_user_agent}
    params = {}

    if start_time:
        start_timestamp = int(start_time.timestamp())
        if window == PriceWindow.FIVE_MINUTES and start_timestamp % 300 != 0:
            start_timestamp = start_timestamp - (start_timestamp % 300)
        elif window == PriceWindow.ONE_HOUR and start_timestamp % 3600 != 0:
            start_timestamp = start_timestamp - (start_timestamp % 3600)
        elif window == PriceWindow.ONE_DAY and start_timestamp % 86400 != 0:
            start_timestamp = start_timestamp - (start_timestamp % 86400)
        params["timestamp"] = start_timestamp

    if window == PriceWindow.FIVE_MINUTES:
        window_param = "5m"
    elif window == PriceWindow.ONE_HOUR:
        window_param = "1h"
    elif window == PriceWindow.ONE_DAY:
        window_param = "24h"
    else:
        raise ValueError(f"Invalid window: {window}")

    async with ClientSession() as session:
        r = await session.get(
            f"{settings.wiki_api_base_url}/{window_param}",
            headers=headers,
            params=params,
        )
        r.raise_for_status()
        r_json = await r.json()
        data = r_json["data"]
        return [
            WindowItemPriceCreate(
                item_source_id=int(k),
                window=window,
                start_timestamp=(
                    datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
                    if start_time
                    else datetime.now(tz=timezone.utc) - timedelta(hours=1)
                ),
                **v,
            )
            for k, v in data.items()
        ]


async def fetch_backfill_prices(
    ctx,
    start_timestamp: datetime = None,
    window: PriceWindow = PriceWindow.FIVE_MINUTES,
):
    """Fetch and upsert windowed price data."""
    total_prices = 0
    data = await fetch_window(window, start_time=start_timestamp)
    db = ctx.get("db")

    for pw in data:
        data_dump = pw.model_dump(exclude_none=True)
        total_volume = (
            (pw.high_price_volume or 0) + (pw.low_price_volume or 0)
            if pw.high_price_volume or pw.low_price_volume
            else None
        )
        data_dump["total_volume"] = total_volume
        await db.itempricewindow.upsert(
            where={
                "item_source_id_window_start_timestamp": {
                    "item_source_id": pw.item_source_id,
                    "window": pw.window,
                    "start_timestamp": pw.start_timestamp,
                }
            },
            data={
                "create": data_dump,
                "update": {
                    "average_high_price": pw.average_high_price,
                    "average_low_price": pw.average_low_price,
                    "high_price_volume": pw.high_price_volume,
                    "low_price_volume": pw.low_price_volume,
                    "total_volume": (
                        (pw.high_price_volume or 0) + (pw.low_price_volume or 0)
                        if pw.high_price_volume or pw.low_price_volume
                        else None
                    ),
                    "created_at": datetime.now(tz=timezone.utc),
                },
            },
        )
        total_prices += 1

    return {
        "result": "success",
        "total_prices": total_prices,
        "start_timestamp": start_timestamp,
        "window": window,
    }
