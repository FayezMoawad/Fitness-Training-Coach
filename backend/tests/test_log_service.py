"""Unit tests for log_service, with the DB session mocked — no real database
involved, per the same pattern used for workout_service in Step 4."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.models.workout import Workout
from app.models.workout_assignment import AssignmentStatus, WorkoutAssignment
from app.schemas.log import ExerciseResult, WorkoutLogCreate
from app.services import log_service


def make_user(user_id: int, role: UserRole) -> User:
    return User(
        id=user_id,
        email=f"user{user_id}@example.com",
        hashed_password="irrelevant",
        role=role,
        full_name="Test User",
    )


def make_log_data() -> WorkoutLogCreate:
    return WorkoutLogCreate(
        exercises=[ExerciseResult(name="Squat", sets=3, reps=10, weight=60)], notes="Felt good"
    )


def test_log_workout_result_persists_and_marks_assignment_completed():
    client_user = make_user(2, UserRole.client)
    assignment = WorkoutAssignment(id=5, workout_id=10, client_id=2, status=AssignmentStatus.assigned)

    db = MagicMock()
    db.get.return_value = assignment

    log = log_service.log_workout_result(db, client_user, assignment_id=5, data=make_log_data())

    assert log.assignment_id == 5
    assert log.exercises == [{"name": "Squat", "sets": 3, "reps": 10, "weight": 60}]
    assert assignment.status == AssignmentStatus.completed
    db.add.assert_called_once_with(log)
    db.commit.assert_called_once()


def test_log_workout_result_raises_when_assignment_missing():
    client_user = make_user(2, UserRole.client)
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(log_service.AssignmentNotFoundError):
        log_service.log_workout_result(db, client_user, assignment_id=999, data=make_log_data())


def test_log_workout_result_raises_404_for_a_different_clients_assignment():
    other_client = make_user(3, UserRole.client)
    assignment = WorkoutAssignment(id=5, workout_id=10, client_id=2)

    db = MagicMock()
    db.get.return_value = assignment

    with pytest.raises(HTTPException) as exc_info:
        log_service.log_workout_result(db, other_client, assignment_id=5, data=make_log_data())
    assert exc_info.value.status_code == 404


def test_get_logs_for_assignment_allows_owning_client():
    client_user = make_user(2, UserRole.client)
    assignment = WorkoutAssignment(id=5, workout_id=10, client_id=2)

    db = MagicMock()
    db.get.return_value = assignment
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = ["log"]

    result = log_service.get_logs_for_assignment(db, client_user, assignment_id=5)

    assert result == ["log"]


def test_get_logs_for_assignment_rejects_a_different_client():
    other_client = make_user(3, UserRole.client)
    assignment = WorkoutAssignment(id=5, workout_id=10, client_id=2)

    db = MagicMock()
    db.get.return_value = assignment

    with pytest.raises(HTTPException) as exc_info:
        log_service.get_logs_for_assignment(db, other_client, assignment_id=5)
    assert exc_info.value.status_code == 404


def test_get_logs_for_assignment_allows_the_assigning_coach():
    coach = make_user(1, UserRole.coach)
    assignment = WorkoutAssignment(id=5, workout_id=10, client_id=2)
    workout = Workout(id=10, coach_id=1, name="Leg Day")

    db = MagicMock()
    db.get.side_effect = lambda model, id_: assignment if model is WorkoutAssignment else workout
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = ["log"]

    result = log_service.get_logs_for_assignment(db, coach, assignment_id=5)

    assert result == ["log"]


def test_get_logs_for_assignment_rejects_a_different_coach():
    other_coach = make_user(4, UserRole.coach)
    assignment = WorkoutAssignment(id=5, workout_id=10, client_id=2)
    workout = Workout(id=10, coach_id=1, name="Leg Day")

    db = MagicMock()
    db.get.side_effect = lambda model, id_: assignment if model is WorkoutAssignment else workout

    with pytest.raises(HTTPException) as exc_info:
        log_service.get_logs_for_assignment(db, other_coach, assignment_id=5)
    assert exc_info.value.status_code == 404
