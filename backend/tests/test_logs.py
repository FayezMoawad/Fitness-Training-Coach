"""Integration tests for the workout-log endpoints: log -> completed
transition, ownership/role enforcement, and error-response hygiene."""

from tests.test_workouts import auth_headers_for_client, auth_headers_for_coach, get_user_id


def create_assigned_workout(client, coach_headers: dict, client_id: int) -> dict:
    workout = client.post("/workouts", json={"name": "Leg Day"}, headers=coach_headers).json()
    return client.post(
        f"/workouts/{workout['id']}/assign",
        json={"client_id": client_id},
        headers=coach_headers,
    ).json()


def log_payload(**overrides):
    payload = {
        "exercises": [{"name": "Squat", "sets": 3, "reps": 10, "weight": 60}],
        "notes": "Felt strong",
    }
    payload.update(overrides)
    return payload


def test_client_logs_results_for_own_assignment_marks_completed(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    assignment = create_assigned_workout(client, coach_headers, client_id)

    response = client.post(
        f"/assignments/{assignment['id']}/logs", json=log_payload(), headers=client_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["assignment_id"] == assignment["id"]
    assert body["exercises"][0]["name"] == "Squat"

    assignments = client.get("/assignments", headers=client_headers).json()
    assert assignments[0]["status"] == "completed"


def test_client_cannot_log_results_for_another_clients_assignment(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    other_client_headers = auth_headers_for_client(client, email="other-client@example.com")
    client_id = get_user_id(client, client_headers)
    assignment = create_assigned_workout(client, coach_headers, client_id)

    response = client.post(
        f"/assignments/{assignment['id']}/logs", json=log_payload(), headers=other_client_headers
    )

    assert response.status_code == 404


def test_log_with_negative_reps_returns_422(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    assignment = create_assigned_workout(client, coach_headers, client_id)

    response = client.post(
        f"/assignments/{assignment['id']}/logs",
        json=log_payload(exercises=[{"name": "Squat", "sets": 3, "reps": -5, "weight": 60}]),
        headers=client_headers,
    )

    assert response.status_code == 422


def test_log_with_no_exercises_returns_422(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    assignment = create_assigned_workout(client, coach_headers, client_id)

    response = client.post(
        f"/assignments/{assignment['id']}/logs",
        json=log_payload(exercises=[]),
        headers=client_headers,
    )

    assert response.status_code == 422


def test_coach_cannot_post_logs_returns_403(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    assignment = create_assigned_workout(client, coach_headers, client_id)

    response = client.post(
        f"/assignments/{assignment['id']}/logs", json=log_payload(), headers=coach_headers
    )

    assert response.status_code == 403


def test_coach_fetches_logs_for_their_assigned_client(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    assignment = create_assigned_workout(client, coach_headers, client_id)
    client.post(f"/assignments/{assignment['id']}/logs", json=log_payload(), headers=client_headers)

    response = client.get(f"/assignments/{assignment['id']}/logs", headers=coach_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["exercises"][0]["name"] == "Squat"


def test_other_coach_cannot_fetch_logs_returns_404(client):
    coach_headers = auth_headers_for_coach(client)
    other_coach_headers = auth_headers_for_coach(client, email="other-coach@example.com")
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    assignment = create_assigned_workout(client, coach_headers, client_id)
    client.post(f"/assignments/{assignment['id']}/logs", json=log_payload(), headers=client_headers)

    response = client.get(f"/assignments/{assignment['id']}/logs", headers=other_coach_headers)

    assert response.status_code == 404


def test_logging_to_nonexistent_assignment_returns_404(client):
    client_headers = auth_headers_for_client(client)

    response = client.post(
        "/assignments/999999/logs", json=log_payload(), headers=client_headers
    )

    assert response.status_code == 404


def test_db_failure_during_log_creation_returns_generic_500_with_no_leak(
    client, db_session, monkeypatch
):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    assignment = create_assigned_workout(client, coach_headers, client_id)

    def broken_commit():
        raise RuntimeError(
            'psycopg.errors.UndefinedTable: relation "workout_logs" does not exist'
        )

    monkeypatch.setattr(db_session, "commit", broken_commit)

    from fastapi.testclient import TestClient

    from app.main import app

    no_raise_client = TestClient(app, raise_server_exceptions=False)
    response = no_raise_client.post(
        f"/assignments/{assignment['id']}/logs", json=log_payload(), headers=client_headers
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "psycopg" not in response.text
    assert "UndefinedTable" not in response.text
    assert "Traceback" not in response.text
