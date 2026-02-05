"""Item-related Pydantic models."""

from pydantic import BaseModel, Field, ConfigDict
from prisma.enums import ItemType
from typing import Optional


class ItemCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    source_id: int = Field(..., description="The source ID of the item", alias="id")
    name: str
    is_members: bool = Field(
        default=False, description="Whether the item is a members item", alias="members"
    )
    low_alch_price: int = Field(
        default=0, description="The low alch price of the item", alias="lowalch"
    )
    high_alch_price: int = Field(
        default=0, description="The high alch price of the item", alias="highalch"
    )
    ge_buy_limit: int = Field(
        default=0, description="The GE buy limit of the item", alias="limit"
    )
    examine_text: str = Field(
        default="", description="The examine text of the item", alias="examine"
    )
    item_type: ItemType = Field(
        description="The type of the item", default=ItemType.UNKNOWN
    )


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    item_type: Optional[ItemType] = None
    track_price: Optional[bool] = None
