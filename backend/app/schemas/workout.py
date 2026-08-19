"""Request/response schemas for creating workouts and assigning them to clients.

Note: the `Workout` model (Step 1) stores only `name`/`description` — there is
no per-exercise structure on the workout itself (that lives on `WorkoutLog`,
populated when a client logs results in Step 5). So `WorkoutCreate` validates
those two fields rather than exercise-level data.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.workout_assignment import AssignmentStatus


class WorkoutCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)


class WorkoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    coach_id: int
    name: str
    description: str | None
    created_at: datetime


class AssignmentCreate(BaseModel):
    client_id: int


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_id: int
    client_id: int
    assigned_at: datetime
    status: AssignmentStatus
