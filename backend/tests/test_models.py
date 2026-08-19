"""Model-level tests: constraints, foreign keys, and uniqueness.

Run against a real PostgreSQL test database (see conftest.py) so that
constraints enforced only by the database (FKs, enum types, unique indexes)
are actually exercised, not just Python-side validation.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError

from app.models import AssignmentStatus, User, UserRole, Workout, WorkoutAssignment, WorkoutLog


def make_user(db_session, *, email="coach@example.com", role=UserRole.coach, full_name="Coach One"):
    user = User(email=email, hashed_password="hashed", role=role, full_name=full_name)
    db_session.add(user)
    db_session.flush()
    return user


def test_create_valid_user(db_session):
    user = make_user(db_session)
    db_session.flush()

    assert user.id is not None
    assert user.role == UserRole.coach
    assert user.created_at is not None


def test_user_email_uniqueness(db_session):
    make_user(db_session, email="dup@example.com")
    db_session.flush()

    dup = User(
        email="dup@example.com",
        hashed_password="hashed",
        role=UserRole.client,
        full_name="Someone Else",
    )
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_invalid_role_rejected_at_db_level(db_session):
    # Bypass the Python Enum to exercise the actual Postgres ENUM constraint.
    with pytest.raises(DataError):
        db_session.execute(
            text(
                "INSERT INTO users (email, hashed_password, role, full_name) "
                "VALUES (:email, 'hashed', 'not_a_role', 'X')"
            ),
            {"email": "bad-role@example.com"},
        )
        db_session.flush()


def test_user_missing_required_field_rejected(db_session):
    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "INSERT INTO users (email, hashed_password, role) "
                "VALUES ('no-name@example.com', 'hashed', 'coach')"
            )
        )
        db_session.flush()


def test_create_workout_for_coach(db_session):
    coach = make_user(db_session)
    workout = Workout(coach_id=coach.id, name="Leg Day", description="Squats and lunges")
    db_session.add(workout)
    db_session.flush()

    assert workout.id is not None
    assert workout.created_at is not None


def test_workout_assignment_rejects_nonexistent_client(db_session):
    coach = make_user(db_session)
    workout = Workout(coach_id=coach.id, name="Push Day")
    db_session.add(workout)
    db_session.flush()

    assignment = WorkoutAssignment(workout_id=workout.id, client_id=999_999)
    db_session.add(assignment)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_workout_assignment_rejects_nonexistent_workout(db_session):
    client = make_user(db_session, email="client@example.com", role=UserRole.client, full_name="Client One")

    assignment = WorkoutAssignment(workout_id=999_999, client_id=client.id)
    db_session.add(assignment)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_workout_assignment_defaults_to_assigned_status(db_session):
    coach = make_user(db_session)
    client = make_user(db_session, email="client2@example.com", role=UserRole.client, full_name="Client Two")
    workout = Workout(coach_id=coach.id, name="Pull Day")
    db_session.add(workout)
    db_session.flush()

    assignment = WorkoutAssignment(workout_id=workout.id, client_id=client.id)
    db_session.add(assignment)
    db_session.flush()

    assert assignment.status == AssignmentStatus.assigned
    assert assignment.assigned_at is not None


def test_workout_log_requires_valid_assignment(db_session):
    log = WorkoutLog(assignment_id=999_999, exercises=[{"name": "Squat", "sets": 3, "reps": 10, "weight": 100}])
    db_session.add(log)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_workout_log_persists_and_updates_status(db_session):
    coach = make_user(db_session)
    client = make_user(db_session, email="client3@example.com", role=UserRole.client, full_name="Client Three")
    workout = Workout(coach_id=coach.id, name="Full Body")
    db_session.add(workout)
    db_session.flush()

    assignment = WorkoutAssignment(workout_id=workout.id, client_id=client.id)
    db_session.add(assignment)
    db_session.flush()

    log = WorkoutLog(
        assignment_id=assignment.id,
        exercises=[{"name": "Deadlift", "sets": 3, "reps": 5, "weight": 135}],
        notes="Felt good",
    )
    assignment.status = AssignmentStatus.completed
    db_session.add(log)
    db_session.flush()

    assert log.id is not None
    assert log.exercises[0]["name"] == "Deadlift"
    assert assignment.status == AssignmentStatus.completed


def test_deleting_user_cascades_to_workouts(db_session):
    coach = make_user(db_session, email="cascade-coach@example.com")
    workout = Workout(coach_id=coach.id, name="Cascade Test")
    db_session.add(workout)
    db_session.flush()
    workout_id = workout.id

    db_session.delete(coach)
    db_session.flush()

    # Query the row count directly rather than session.get(), which would
    # return the stale object already cached in the identity map instead of
    # re-checking the database (ORM sessions don't track DB-level FK
    # cascades that happen outside the session's own delete tracking).
    remaining_count = db_session.execute(
        text("SELECT count(*) FROM workouts WHERE id = :id"), {"id": workout_id}
    ).scalar_one()
    assert remaining_count == 0
