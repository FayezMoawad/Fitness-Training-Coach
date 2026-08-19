"""Request/response schemas for logging a client's workout results."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExerciseResult(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sets: int = Field(gt=0)
    reps: int = Field(gt=0)
    weight: float = Field(ge=0)


class WorkoutLogCreate(BaseModel):
    exercises: list[ExerciseResult] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=10_000)


class WorkoutLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    exercises: list[ExerciseResult]
    notes: str | None
    logged_at: datetime
