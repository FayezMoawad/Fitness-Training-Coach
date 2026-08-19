"""Integration tests for GET /clients/{client_id}/progress."""

from tests.test_workouts import auth_headers_for_client, auth_headers_for_coach, get_user_id


def create_assigned_workout(client, coach_headers: dict, client_id: int, name: str = "Leg Day") -> dict:
    workout = client.post("/workouts", json={"name": name}, headers=coach_headers).json()
    return client.post(
        f"/workouts/{workout['id']}/assign",
        json={"client_id": client_id},
        headers=coach_headers,
    ).json()


def test_coach_views_progress_for_their_own_client(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    assignment = create_assigned_workout(client, coach_headers, client_id)
    client.post(
        f"/assignments/{assignment['id']}/logs",
        json={"exercises": [{"name": "Squat", "sets": 3, "reps": 10, "weight": 60}]},
        headers=client_headers,
    )

    response = client.get(f"/clients/{client_id}/progress", headers=coach_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["client_id"] == client_id
    assert len(body["assignments"]) == 1
    entry = body["assignments"][0]
    assert entry["workout_name"] == "Leg Day"
    assert entry["status"] == "completed"
    assert len(entry["logs"]) == 1
    assert entry["logs"][0]["exercises"][0]["name"] == "Squat"


def test_coach_views_progress_for_client_with_no_logs_yet(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    create_assigned_workout(client, coach_headers, client_id)

    response = client.get(f"/clients/{client_id}/progress", headers=coach_headers)

    assert response.status_code == 200
    assert response.json()["assignments"][0]["logs"] == []


def test_coach_requests_progress_for_client_never_assigned_anything_returns_404(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)

    response = client.get(f"/clients/{client_id}/progress", headers=coach_headers)

    assert response.status_code == 404


def test_coach_cannot_view_another_coachs_client_progress(client):
    coach_headers = auth_headers_for_coach(client)
    other_coach_headers = auth_headers_for_coach(client, email="other-coach@example.com")
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    create_assigned_workout(client, coach_headers, client_id)

    response = client.get(f"/clients/{client_id}/progress", headers=other_coach_headers)

    assert response.status_code == 404


def test_client_cannot_call_progress_endpoint_returns_403(client):
    client_headers = auth_headers_for_client(client)

    response = client.get("/clients/1/progress", headers=client_headers)

    assert response.status_code == 403


def test_progress_orders_assignments_chronologically(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)
    create_assigned_workout(client, coach_headers, client_id, name="First")
    create_assigned_workout(client, coach_headers, client_id, name="Second")

    response = client.get(f"/clients/{client_id}/progress", headers=coach_headers)

    names = [a["workout_name"] for a in response.json()["assignments"]]
    assert names == ["First", "Second"]
