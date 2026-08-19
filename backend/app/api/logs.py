"""Workout-log routes — thin, delegate to log_service.

`GET` is shared by both roles: the owning client and the coach who assigned
the workout can both read the logs; `get_logs_for_assignment` picks the right
ownership check based on the caller's role.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.log import WorkoutLogCreate, WorkoutLogResponse
from app.services import log_service

router = APIRouter(tags=["logs"])


@router.post(
    "/assignments/{assignment_id}/logs",
    response_model=WorkoutLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_log(
    assignment_id: int,
    data: WorkoutLogCreate,
    client: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
):
    try:
        return log_service.log_workout_result(db, client, assignment_id, data)
    except log_service.AssignmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        ) from None


@router.get("/assignments/{assignment_id}/logs", response_model=list[WorkoutLogResponse])
def list_logs(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return log_service.get_logs_for_assignment(db, current_user, assignment_id)
    except log_service.AssignmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        ) from None
