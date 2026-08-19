"""Unit tests for role and ownership guards, in isolation from any route or
DB — these operate on plain in-memory model instances and call the
dependency/helper functions directly, per the plan's Step 3 done criteria
("unit-tested in isolation before being wired into real endpoints")."""

import pytest
from fastapi import HTTPException

from app.core.deps import require_role
from app.models.user import User, UserRole
from app.models.workout import Workout
from app.models.workout_assignment import WorkoutAssignment
from app.services.authorization import assert_client_owns_assignment, assert_coach_owns_workout


def make_user(user_id: int, role: UserRole) -> User:
    return User(
        id=user_id,
        email=f"user{user_id}@example.com",
        hashed_password="irrelevant",
        role=role,
        full_name="Test User",
    )


def test_require_role_allows_matching_role():
    coach = make_user(1, UserRole.coach)
    guard = require_role(UserRole.coach)

    assert guard(current_user=coach) is coach


def test_require_role_rejects_client_on_coach_only_route():
    client_user = make_user(2, UserRole.client)
    guard = require_role(UserRole.coach)

    with pytest.raises(HTTPException) as exc_info:
        guard(current_user=client_user)
    assert exc_info.value.status_code == 403


def test_require_role_rejects_coach_on_client_only_route():
    coach = make_user(1, UserRole.coach)
    guard = require_role(UserRole.client)

    with pytest.raises(HTTPException) as exc_info:
        guard(current_user=coach)
    assert exc_info.value.status_code == 403


def test_assert_coach_owns_workout_passes_for_the_owning_coach():
    coach = make_user(1, UserRole.coach)
    workout = Workout(id=10, coach_id=1, name="Leg Day")

    assert_coach_owns_workout(workout, coach)  # does not raise


def test_assert_coach_owns_workout_rejects_a_different_coach():
    other_coach = make_user(2, UserRole.coach)
    workout = Workout(id=10, coach_id=1, name="Leg Day")

    with pytest.raises(HTTPException) as exc_info:
        assert_coach_owns_workout(workout, other_coach)
    assert exc_info.value.status_code == 404


def test_assert_client_owns_assignment_passes_for_the_owning_client():
    client_user = make_user(3, UserRole.client)
    assignment = WorkoutAssignment(id=5, workout_id=10, client_id=3)

    assert_client_owns_assignment(assignment, client_user)  # does not raise


def test_assert_client_owns_assignment_rejects_a_different_client():
    client_a = make_user(3, UserRole.client)
    assignment_owned_by_client_b = WorkoutAssignment(id=5, workout_id=10, client_id=4)

    with pytest.raises(HTTPException) as exc_info:
        assert_client_owns_assignment(assignment_owned_by_client_b, client_a)
    assert exc_info.value.status_code == 404
