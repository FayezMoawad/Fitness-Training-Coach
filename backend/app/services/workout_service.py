"""Workout-assignment business logic — kept out of the route layer per CLAUDE.md.

Status code convention: a `workout_id` that doesn't exist and a `workout_id`
that belongs to a *different* coach both raise the same 404 (via
`assert_coach_owns_workout`), so a coach can't distinguish "no such workout"
from "not your workout" — consistent with the 403-vs-404 convention documented
in `app.services.authorization`. An invalid `client_id` (missing, or not a
client) is a caller-input problem rather than an ownership question, so it
raises a distinct error the route maps to 400.
"""

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.workout import Workout
from app.models.workout_assignment import WorkoutAssignment
from app.schemas.workout import AssignmentCreate, WorkoutCreate
from app.services.authorization import assert_coach_owns_workout


class WorkoutNotFoundError(Exception):
    pass


class InvalidClientError(Exception):
    pass


def create_workout(db: Session, coach: User, data: WorkoutCreate) -> Workout:
    workout = Workout(coach_id=coach.id, name=data.name, description=data.description)
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


def assign_workout(
    db: Session, coach: User, workout_id: int, data: AssignmentCreate
) -> WorkoutAssignment:
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise WorkoutNotFoundError()
    assert_coach_owns_workout(workout, coach)

    client = db.get(User, data.client_id)
    if client is None or client.role != UserRole.client:
        raise InvalidClientError()

    assignment = WorkoutAssignment(workout_id=workout.id, client_id=client.id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def list_workouts_for_coach(db: Session, coach: User) -> list[Workout]:
    return (
        db.query(Workout)
        .filter(Workout.coach_id == coach.id)
        .order_by(Workout.created_at.desc())
        .all()
    )


def list_assignments_for_coach(db: Session, coach: User) -> list[WorkoutAssignment]:
    return (
        db.query(WorkoutAssignment)
        .join(Workout, WorkoutAssignment.workout_id == Workout.id)
        .filter(Workout.coach_id == coach.id)
        .order_by(WorkoutAssignment.assigned_at.desc())
        .all()
    )


def list_assignments_for_client(db: Session, client: User) -> list[WorkoutAssignment]:
    return (
        db.query(WorkoutAssignment)
        .filter(WorkoutAssignment.client_id == client.id)
        .order_by(WorkoutAssignment.assigned_at.desc())
        .all()
    )
