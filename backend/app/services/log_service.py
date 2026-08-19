"""Workout-log business logic — kept out of the route layer per CLAUDE.md.

Status code convention: a nonexistent `assignment_id` and one that exists but
isn't the caller's (a different client's, or a different coach's client's)
both raise `AssignmentNotFoundError` -> 404, via the ownership helpers in
`app.services.authorization` — consistent with the 403-vs-404 convention
documented there.
"""

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.workout import Workout
from app.models.workout_assignment import AssignmentStatus, WorkoutAssignment
from app.models.workout_log import WorkoutLog
from app.schemas.log import WorkoutLogCreate
from app.services.authorization import assert_client_owns_assignment, assert_coach_owns_workout


class AssignmentNotFoundError(Exception):
    pass


def log_workout_result(
    db: Session, client: User, assignment_id: int, data: WorkoutLogCreate
) -> WorkoutLog:
    assignment = db.get(WorkoutAssignment, assignment_id)
    if assignment is None:
        raise AssignmentNotFoundError()
    assert_client_owns_assignment(assignment, client)

    log = WorkoutLog(
        assignment_id=assignment.id,
        exercises=[exercise.model_dump() for exercise in data.exercises],
        notes=data.notes,
    )
    db.add(log)
    assignment.status = AssignmentStatus.completed
    db.commit()
    db.refresh(log)
    return log


def get_logs_for_assignment(db: Session, user: User, assignment_id: int) -> list[WorkoutLog]:
    assignment = db.get(WorkoutAssignment, assignment_id)
    if assignment is None:
        raise AssignmentNotFoundError()

    if user.role == UserRole.client:
        assert_client_owns_assignment(assignment, user)
    else:
        workout = db.get(Workout, assignment.workout_id)
        assert_coach_owns_workout(workout, user)

    return (
        db.query(WorkoutLog)
        .filter(WorkoutLog.assignment_id == assignment.id)
        .order_by(WorkoutLog.logged_at.desc())
        .all()
    )
