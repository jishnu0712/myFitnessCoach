"""Validate workout writes and serialize persisted workout records."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkoutCreateRequest(BaseModel):
    """Flexible JSON data supplied for a workout record."""

    model_config = ConfigDict(extra="forbid")

    workout_data: dict[str, Any] = Field(max_length=100)


class WorkoutResponse(BaseModel):
    """Public workout representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_data: dict[str, Any]
    created_at: datetime
