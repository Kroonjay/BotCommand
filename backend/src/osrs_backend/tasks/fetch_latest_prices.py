"""Fetch latest item prices from OSRS Wiki API."""

from aiohttp import ClientSession
from prisma.errors import MissingRequiredValueError, ForeignKeyViolationError
from pydantic import ValidationError
from logging import getLogger

from osrs_backend.models.item_price import ItemPriceCreate
from osrs_backend.config import get_settings

logger = getLogger(__name__)


async def fetch_latest_prices(ctx):
    """Fetch latest prices from the OSRS Wiki API."""
    db = ctx.get("db")
    settings = get_settings()
    url = f"{settings.wiki_api_base_url}/latest"
    headers = {"User-Agent": settings.wiki_api_user_agent}
    total_item_prices = 0

    async with ClientSession() as session:
        response = await session.get(url, headers=headers)
        data = await response.json()
        for key, value in data.get("data").items():
            try:
                value.update({"item_source_id": key})
                item_price = ItemPriceCreate.model_validate(value, by_alias=True)
            except ValidationError as ve:
                logger.error(
                    f"Error validating item price: {ve.json()} | Data: {value}"
                )
                continue
            try:
                await db.itemprice.create(data=item_price.model_dump())
            except MissingRequiredValueError as mrve:
                logger.error(
                    f"Error creating item price: {str(mrve)} | Data: {item_price.model_dump_json()}"
                )
                continue
            except ForeignKeyViolationError as fkve:
                logger.error(
                    f"Error creating item price: {str(fkve)} | Data: {item_price.model_dump_json()}"
                )
                continue
            total_item_prices += 1

    if not total_item_prices:
        logger.error("No Item Prices Found")
    result = {"total_prices": total_item_prices}
    return result
