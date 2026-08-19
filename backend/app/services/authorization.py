"""Reusable ownership-check helpers, for Steps 4–6 to call once a resource
has already been loaded (e.g. `workout = db.get(Workout, workout_id)`).

Status code convention: `require_role` (app.core.deps) returns 403 for a
role mismatch, since the caller already knows their own role — there's
nothing to leak. An ownership violation on a *specific* resource returns
404 instead of 403: if a client could tell "403 forbidden" (exists, not
yours) apart from "404 not found" (doesn't exist), that distinction itself
would leak which resource IDs belong to other users. Steps 4–6 should call
these helpers rather than re-implementing the same check.
"""

from fastapi import HTTPException, status

from app.models.user import User
from app.models.workout import Workout
from app.models.workout_assignment import WorkoutAssignment


def assert_coach_owns_workout(workout: Workout, user: User) -> None:
    if workout.coach_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")


def assert_client_owns_assignment(assignment: WorkoutAssignment, user: User) -> None:
    if assignment.client_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )
