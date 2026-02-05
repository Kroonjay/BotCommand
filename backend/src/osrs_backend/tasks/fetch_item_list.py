"""Fetch item list from OSRS Wiki API."""

from aiohttp import ClientSession
from logging import getLogger
from pydantic import ValidationError

from osrs_backend.models.item import ItemCreate
from osrs_backend.config import get_settings

logger = getLogger(__name__)


async def fetch_item_list(ctx):
    """Fetch and sync item list from the OSRS Wiki API."""
    db = ctx.get("db")
    settings = get_settings()
    headers = {"User-Agent": settings.wiki_api_user_agent}
    total_items = 0
    url = f"{settings.wiki_api_base_url}/mapping"

    async with ClientSession() as session:
        items = await session.get(url, headers=headers)
        items = await items.json()
        for item in items:
            try:
                item_data = ItemCreate.model_validate(item, by_alias=True)
            except ValidationError as e:
                logger.error(f"Error validating item: {e.json()}")
                continue
            await db.item.upsert(
                where={"source_id": item_data.source_id},
                data={
                    "create": item_data.model_dump(),
                    "update": item_data.model_dump(
                        include={
                            "name",
                            "low_alch_price",
                            "high_alch_price",
                            "ge_buy_limit",
                            "examine_text",
                        }
                    ),
                },
            )
            total_items += 1
    return {"total_items": total_items}
