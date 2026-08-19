"""Unit tests for workout_service, with the DB session mocked — no real
database involved, per the plan's Step 4 request for isolated service-layer
tests."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.models.workout import Workout
from app.schemas.workout import AssignmentCreate, WorkoutCreate
from app.services import workout_service


def make_user(user_id: int, role: UserRole) -> User:
    return User(
        id=user_id,
        email=f"user{user_id}@example.com",
        hashed_password="irrelevant",
        role=role,
        full_name="Test User",
    )


def test_create_workout_persists_with_coach_id():
    db = MagicMock()
    coach = make_user(1, UserRole.coach)

    workout = workout_service.create_workout(
        db, coach, WorkoutCreate(name="Leg Day", description="Squats and lunges")
    )

    assert workout.coach_id == 1
    assert workout.name == "Leg Day"
    assert workout.description == "Squats and lunges"
    db.add.assert_called_once_with(workout)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(workout)


def test_assign_workout_creates_assignment_for_valid_client():
    coach = make_user(1, UserRole.coach)
    client_user = make_user(2, UserRole.client)
    workout = Workout(id=10, coach_id=1, name="Leg Day")

    db = MagicMock()
    db.get.side_effect = lambda model, id_: workout if model is Workout else client_user

    assignment = workout_service.assign_workout(
        db, coach, workout_id=10, data=AssignmentCreate(client_id=2)
    )

    assert assignment.workout_id == 10
    assert assignment.client_id == 2
    db.add.assert_called_once_with(assignment)
    db.commit.assert_called_once()


def test_assign_workout_raises_when_workout_missing():
    coach = make_user(1, UserRole.coach)
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(workout_service.WorkoutNotFoundError):
        workout_service.assign_workout(db, coach, workout_id=999, data=AssignmentCreate(client_id=2))


def test_assign_workout_raises_403_for_a_different_coachs_workout():
    other_coach = make_user(2, UserRole.coach)
    workout = Workout(id=10, coach_id=1, name="Leg Day")

    db = MagicMock()
    db.get.return_value = workout

    with pytest.raises(HTTPException) as exc_info:
        workout_service.assign_workout(
            db, other_coach, workout_id=10, data=AssignmentCreate(client_id=2)
        )
    assert exc_info.value.status_code == 404


def test_assign_workout_raises_when_client_id_is_not_a_client():
    coach = make_user(1, UserRole.coach)
    workout = Workout(id=10, coach_id=1, name="Leg Day")
    other_coach = make_user(3, UserRole.coach)

    db = MagicMock()
    db.get.side_effect = lambda model, id_: workout if model is Workout else other_coach

    with pytest.raises(workout_service.InvalidClientError):
        workout_service.assign_workout(db, coach, workout_id=10, data=AssignmentCreate(client_id=3))


def test_assign_workout_raises_when_client_id_does_not_exist():
    coach = make_user(1, UserRole.coach)
    workout = Workout(id=10, coach_id=1, name="Leg Day")

    db = MagicMock()
    db.get.side_effect = lambda model, id_: workout if model is Workout else None

    with pytest.raises(workout_service.InvalidClientError):
        workout_service.assign_workout(db, coach, workout_id=10, data=AssignmentCreate(client_id=999))
