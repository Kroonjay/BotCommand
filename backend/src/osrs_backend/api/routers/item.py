"""Item-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from prisma.models import Item, ItemPrice
from prisma import Prisma
from prisma.errors import UniqueViolationError
from logging import getLogger

from osrs_backend.db.database import get_db
from osrs_backend.models.item import ItemCreate, ItemUpdate
from osrs_backend.models.item_price import ItemPriceCreate

logger = getLogger(__name__)

router = APIRouter(
    prefix="/items",
    tags=["items"],
)


@router.get("/", response_model=List[Item], response_model_exclude_none=True)
async def get_items(db: Prisma = Depends(get_db), limit: int = 100):
    items = await db.item.find_many(order={"id": "desc"}, take=limit)
    return items


@router.get("/view/{item_id}", response_model=Item, response_model_exclude_none=True)
async def get_item(item_id: int, db: Prisma = Depends(get_db)):
    item = await db.item.find_unique(where={"id": item_id})
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} not found"
        )
    return item


@router.get("/search", response_model=Item, response_model_exclude_none=True)
async def get_item_by_name(name: str, db: Prisma = Depends(get_db)):
    item = await db.item.find_first(where={"name": name})
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {name} not found"
        )
    return item


@router.put("/{item_id}", response_model=Item, response_model_exclude_none=True)
async def update_item(item_id: int, item: ItemUpdate, db: Prisma = Depends(get_db)):
    item = await db.item.update(
        where={"id": item_id}, data=item.model_dump(exclude_none=True)
    )
    return item


@router.post("/", response_model=Item)
async def create_item(item: ItemCreate, db: Prisma = Depends(get_db)):
    try:
        item = await db.item.create(item.model_dump())
    except UniqueViolationError as uve:
        logger.error(f"Failed to Create Item | Unique Violation Error: {uve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item {item.name} already exists",
        )
    return item


@router.get("/current-price", response_model=ItemPrice)
async def get_item_current_price(item_source_id: int, db: Prisma = Depends(get_db)):
    item_price = await db.itemprice.find_first(
        where={"item_source_id": item_source_id}, order={"created_at": "desc"}
    )
    if not item_price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No item found for provided Item Source ID:",
        )
    return item_price


@router.post("/current-price", response_model=ItemPrice)
async def create_item_current_price(
    item_price: ItemPriceCreate, db: Prisma = Depends(get_db)
):
    item_price = await db.itemprice.create(item_price.model_dump())
    return item_price
