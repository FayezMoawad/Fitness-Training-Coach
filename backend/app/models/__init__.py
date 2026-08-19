"""Import all models here so `Base.metadata` (and Alembic autogenerate) sees them."""

from app.core.db import Base
from app.models.user import User, UserRole
from app.models.workout import Workout
from app.models.workout_assignment import AssignmentStatus, WorkoutAssignment
from app.models.workout_log import WorkoutLog

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Workout",
    "WorkoutAssignment",
    "AssignmentStatus",
    "WorkoutLog",
]
