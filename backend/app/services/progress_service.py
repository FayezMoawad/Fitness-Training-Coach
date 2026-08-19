"""Progress-review business logic — kept out of the route layer per CLAUDE.md.

Status code convention: a `client_id` the coach has never assigned anything
to raises `NoClientRelationshipError` -> 404, whether that's because the id
doesn't exist at all or belongs to a real client with no relationship to this
coach -- same "don't leak which ids exist" reasoning as the ownership helpers
in `app.services.authorization`.
"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workout import Workout
from app.models.workout_assignment import WorkoutAssignment
from app.models.workout_log import WorkoutLog


class NoClientRelationshipError(Exception):
    pass


def get_client_progress(db: Session, coach: User, client_id: int) -> dict:
    rows = (
        db.query(WorkoutAssignment, Workout.name)
        .join(Workout, WorkoutAssignment.workout_id == Workout.id)
        .filter(Workout.coach_id == coach.id, WorkoutAssignment.client_id == client_id)
        .order_by(WorkoutAssignment.assigned_at.asc())
        .all()
    )
    if not rows:
        raise NoClientRelationshipError()

    assignments = []
    for assignment, workout_name in rows:
        logs = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.assignment_id == assignment.id)
            .order_by(WorkoutLog.logged_at.asc())
            .all()
        )
        assignments.append(
            {
                "assignment_id": assignment.id,
                "workout_id": assignment.workout_id,
                "workout_name": workout_name,
                "status": assignment.status,
                "assigned_at": assignment.assigned_at,
                "logs": logs,
            }
        )

    return {"client_id": client_id, "assignments": assignments}
