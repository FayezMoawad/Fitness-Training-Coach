"""Unit tests for progress_service, with the DB session mocked — no real
database involved, same pattern used for workout_service and log_service."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.models.user import User, UserRole
from app.models.workout import Workout
from app.models.workout_assignment import AssignmentStatus, WorkoutAssignment
from app.models.workout_log import WorkoutLog
from app.services import progress_service


def make_user(user_id: int, role: UserRole) -> User:
    return User(
        id=user_id,
        email=f"user{user_id}@example.com",
        hashed_password="irrelevant",
        role=role,
        full_name="Test User",
    )


def make_mocked_db(rows, logs):
    """A MagicMock db whose `.query(...)` behaves differently depending on
    whether it's the assignments-joined-with-workout-name query or the
    per-assignment logs query, matching what progress_service actually calls."""

    def query_side_effect(*args):
        chain = MagicMock()
        if args and args[0] is WorkoutAssignment and len(args) > 1:
            chain.join.return_value.filter.return_value.order_by.return_value.all.return_value = rows
        else:
            chain.filter.return_value.order_by.return_value.all.return_value = logs
        return chain

    db = MagicMock()
    db.query.side_effect = query_side_effect
    return db


def test_get_client_progress_returns_scoped_assignments_with_nested_logs():
    coach = make_user(1, UserRole.coach)
    assignment = WorkoutAssignment(
        id=5,
        workout_id=10,
        client_id=2,
        status=AssignmentStatus.completed,
        assigned_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    log = WorkoutLog(
        id=1,
        assignment_id=5,
        exercises=[{"name": "Squat", "sets": 3, "reps": 10, "weight": 60}],
        notes=None,
        logged_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    db = make_mocked_db(rows=[(assignment, "Leg Day")], logs=[log])

    result = progress_service.get_client_progress(db, coach, client_id=2)

    assert result["client_id"] == 2
    assert len(result["assignments"]) == 1
    entry = result["assignments"][0]
    assert entry["workout_name"] == "Leg Day"
    assert entry["status"] == AssignmentStatus.completed
    assert entry["logs"] == [log]


def test_get_client_progress_handles_zero_logs_without_error():
    coach = make_user(1, UserRole.coach)
    assignment = WorkoutAssignment(
        id=5,
        workout_id=10,
        client_id=2,
        status=AssignmentStatus.assigned,
        assigned_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    db = make_mocked_db(rows=[(assignment, "Leg Day")], logs=[])

    result = progress_service.get_client_progress(db, coach, client_id=2)

    assert result["assignments"][0]["logs"] == []


def test_get_client_progress_raises_when_coach_never_assigned_this_client():
    coach = make_user(1, UserRole.coach)
    db = make_mocked_db(rows=[], logs=[])

    with pytest.raises(progress_service.NoClientRelationshipError):
        progress_service.get_client_progress(db, coach, client_id=999)
