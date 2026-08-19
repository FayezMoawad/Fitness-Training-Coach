"""Response schema for a coach reviewing a client's progress."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.workout_assignment import AssignmentStatus
from app.schemas.log import WorkoutLogResponse


class ClientProgressAssignment(BaseModel):
    assignment_id: int
    workout_id: int
    workout_name: str
    status: AssignmentStatus
    assigned_at: datetime
    logs: list[WorkoutLogResponse]


class ClientProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id: int
    assignments: list[ClientProgressAssignment]
