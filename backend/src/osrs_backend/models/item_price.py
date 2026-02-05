"""Item price-related Pydantic models."""

from datetime import datetime, timezone, timedelta
from typing import Union, Optional
from pydantic import (
    BaseModel,
    field_validator,
    Field,
    model_validator,
    ValidationError,
    ConfigDict,
)

from osrs_backend.utils.price_parser import price_validator
from prisma.enums import PriceWindow


class ItemPriceCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    item_source_id: int = Field(..., description="The source ID of the item")
    high_price: int = Field(default=0, alias="high")
    low_price: int = Field(default=0, alias="low")
    low_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc), alias="lowTime"
    )
    high_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc), alias="highTime"
    )
    average_price: int = Field(default=0, description="Mean of high and low prices")
    average_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Midpoint between high and low timestamps",
    )

    @field_validator("low_timestamp", "high_timestamp", mode="before")
    @classmethod
    def default_missing_timestamp(
        cls, value: Optional[Union[int, float, datetime]]
    ) -> datetime:
        if value is None or (isinstance(value, str) and not value.strip()):
            return datetime.now(tz=timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        return value

    @model_validator(mode="after")
    def compute_averages(cls, data: "ItemPriceCreate") -> "ItemPriceCreate":
        high_price = data.high_price
        low_price = data.low_price

        high_is_valid = high_price not in (None, 0)
        low_is_valid = low_price not in (None, 0)

        if high_is_valid and low_is_valid:
            data.average_price = int((high_price + low_price) / 2)
        elif high_is_valid:
            data.average_price = high_price
        elif low_is_valid:
            data.average_price = low_price
        else:
            raise ValidationError("Both high and low prices cannot be zero")

        high_ts = data.high_timestamp
        low_ts = data.low_timestamp
        if high_ts and low_ts:
            data.average_timestamp = low_ts + (high_ts - low_ts) / 2
        else:
            data.average_timestamp = high_ts or low_ts or datetime.now(tz=timezone.utc)

        return data

    @field_validator("high_price", "low_price", mode="before")
    @classmethod
    def parse_average_prices(cls, value: Union[str, int, None]) -> int:
        if value is None:
            return 0
        return price_validator(value)


class WindowItemPriceCreate(BaseModel):
    item_source_id: int
    window: PriceWindow
    start_timestamp: datetime = Field(
        alias="timestamp",
        default_factory=lambda: datetime.now(tz=timezone.utc) - timedelta(hours=1),
    )
    average_high_price: Optional[int] = Field(default=0, alias="avgHighPrice")
    average_low_price: Optional[int] = Field(default=0, alias="avgLowPrice")
    high_price_volume: Optional[int] = Field(default=0, alias="highPriceVolume")
    low_price_volume: Optional[int] = Field(default=0, alias="lowPriceVolume")


class DerivedStats(BaseModel):
    item_source_id: int
    window: PriceWindow
    start_timestamp: datetime
    spread: float
    volatility: float
    zscore: float
    latest_price: float
