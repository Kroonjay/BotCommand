"""Healthcheck payload models for DreamBot scripts."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict


class HealthCheckPayload(BaseModel):
    model_config = ConfigDict(
        extra="allow",  # allow future fields without failing
    )

    instance_id: str = Field(alias="instanceId")
    timestamp: int = Field(alias="timestamp")
    task: str = Field(alias="task")

    hp: int = Field(alias="hp")
    x: int = Field(alias="x")
    y: int = Field(alias="y")
    plane: int = Field(alias="plane")

    in_combat: bool = Field(alias="inCombat")
    inventory_count: int = Field(alias="inventoryCount")
    run_energy: int = Field(alias="runEnergy")

    xp_gained: Dict[str, int] = Field(alias="xpGained")
