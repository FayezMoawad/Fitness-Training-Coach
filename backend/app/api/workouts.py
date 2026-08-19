"""Workout and assignment routes — thin, delegate to workout_service.

`GET /assignments` is shared by both roles (coach: workouts they've assigned
out; client: workouts assigned to them — reused as-is by Steps 5/6), so it
only requires *some* authenticated user rather than a specific role.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.workout import Workout
from app.schemas.workout import (
    AssignmentCreate,
    AssignmentResponse,
    WorkoutCreate,
    WorkoutResponse,
)
from app.services import workout_service

router = APIRouter(tags=["workouts"])


@router.post("/workouts", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create_workout(
    data: WorkoutCreate,
    coach: User = Depends(require_role(UserRole.coach)),
    db: Session = Depends(get_db),
) -> Workout:
    return workout_service.create_workout(db, coach, data)


@router.post(
    "/workouts/{workout_id}/assign",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_workout(
    workout_id: int,
    data: AssignmentCreate,
    coach: User = Depends(require_role(UserRole.coach)),
    db: Session = Depends(get_db),
):
    try:
        return workout_service.assign_workout(db, coach, workout_id, data)
    except workout_service.WorkoutNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found"
        ) from None
    except workout_service.InvalidClientError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id must refer to an existing client",
        ) from None


@router.get("/workouts", response_model=list[WorkoutResponse])
def list_workouts(
    coach: User = Depends(require_role(UserRole.coach)),
    db: Session = Depends(get_db),
) -> list[Workout]:
    return workout_service.list_workouts_for_coach(db, coach)


@router.get("/assignments", response_model=list[AssignmentResponse])
def list_assignments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.coach:
        return workout_service.list_assignments_for_coach(db, current_user)
    return workout_service.list_assignments_for_client(db, current_user)
