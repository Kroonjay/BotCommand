"""Pydantic models for the OSRS backend."""

from .item import ItemCreate, ItemUpdate
from .item_price import ItemPriceCreate, WindowItemPriceCreate, DerivedStats
from .healthcheck import HealthCheckPayload
from .action_requirement import (
    Action,
    ActionInput,
    ActionOutput,
    ActionRequirement,
    SkillRequirement,
    ItemRequirement,
    QuestRequirement,
)
from .action import (
    ActionCreate,
    RequirementCreate,
    InputCreate,
    OutputCreate,
    create_action_with_requirements,
    get_action_with_requirements,
    action_to_pydantic,
    _requirement_to_prisma_data,
)

__all__ = [
    "ItemCreate",
    "ItemUpdate",
    "ItemPriceCreate",
    "WindowItemPriceCreate",
    "DerivedStats",
    "HealthCheckPayload",
    "Action",
    "ActionInput",
    "ActionOutput",
    "ActionRequirement",
    "SkillRequirement",
    "ItemRequirement",
    "QuestRequirement",
    "ActionCreate",
    "RequirementCreate",
    "InputCreate",
    "OutputCreate",
    "create_action_with_requirements",
    "get_action_with_requirements",
    "action_to_pydantic",
    "_requirement_to_prisma_data",
]
