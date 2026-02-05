"""Price and percentage string parsing utilities."""

import re
from typing import Union

from prisma.enums import PriceTrend


def parse_price_string(price_str: str) -> int:
    """
    Parse a price string like "1.4m" or "15.7k" into its numerical value.

    Examples:
        "1.4m" -> 1400000
        "15.7k" -> 15700
        "- 15.7k" -> -15700
        "1.2b" -> 1200000000
    """
    if not price_str or not isinstance(price_str, str):
        return 0

    price_str = price_str.strip()
    if not price_str:
        return 0

    is_negative = price_str.startswith("-")
    if is_negative:
        price_str = price_str.lstrip("-").strip()

    match = re.match(r"^([\d.]+)\s*([kmbKMMB]?)", price_str)
    if not match:
        try:
            value = float(price_str)
            return int(value * (-1 if is_negative else 1))
        except ValueError:
            return 0

    number_str = match.group(1)
    suffix = match.group(2).lower() if match.group(2) else ""

    try:
        number = float(number_str)
    except ValueError:
        return 0

    multipliers = {
        "k": 1_000,
        "m": 1_000_000,
        "b": 1_000_000_000,
    }

    multiplier = multipliers.get(suffix, 1)
    result = int(number * multiplier)

    return -result if is_negative else result


def parse_percentage_string(percentage_str: str) -> float:
    """
    Parse a percentage string like "-15.7%" or "10.0%" into its numerical value.
    """
    if not percentage_str or not isinstance(percentage_str, str):
        return 0.0

    percentage_str = percentage_str.strip()
    if not percentage_str:
        return 0.0

    is_negative = percentage_str.startswith("-")
    if is_negative:
        percentage_str = percentage_str.lstrip("-").strip()

    percentage_str = percentage_str.rstrip("%").strip()

    try:
        number = float(percentage_str)
        return -number if is_negative else number
    except ValueError:
        return 0.0


def price_validator(value: Union[str, int]) -> int:
    """Pydantic validator that converts price strings to integers."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return parse_price_string(value)
    return 0


def percentage_validator(value: Union[str, float, int]) -> float:
    """Pydantic validator that converts percentage strings to floats."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return parse_percentage_string(value)
    return 0.0


def trend_validator(value: str) -> PriceTrend:
    """Pydantic validator that converts trend strings to PriceTrend enum."""
    if value == "positive":
        return PriceTrend.POSITIVE
    elif value == "negative":
        return PriceTrend.NEGATIVE
    else:
        return PriceTrend.NEUTRAL
