"""Integration tests for the workout-assignment endpoints:
create → assign → list, plus role/ownership enforcement."""


def signup_and_login(client, *, email: str, role: str, full_name: str = "Test User") -> dict:
    client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": "supersecret1",
            "full_name": full_name,
            "role": role,
        },
    )
    login = client.post("/auth/login", json={"email": email, "password": "supersecret1"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def auth_headers_for_coach(client, email: str = "coach@example.com") -> dict:
    return signup_and_login(client, email=email, role="coach")


def auth_headers_for_client(client, email: str = "client@example.com") -> dict:
    return signup_and_login(client, email=email, role="client")


def get_user_id(client, headers: dict) -> int:
    return client.get("/auth/me", headers=headers).json()["id"]


def test_coach_creates_workout_returns_201_with_correct_coach_id(client):
    coach_headers = auth_headers_for_coach(client)
    coach_id = get_user_id(client, coach_headers)

    response = client.post(
        "/workouts",
        json={"name": "Leg Day", "description": "Squats and lunges"},
        headers=coach_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Leg Day"
    assert body["coach_id"] == coach_id


def test_coach_assigns_workout_to_valid_client_returns_201_assigned(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)

    workout = client.post(
        "/workouts", json={"name": "Leg Day"}, headers=coach_headers
    ).json()

    response = client.post(
        f"/workouts/{workout['id']}/assign",
        json={"client_id": client_id},
        headers=coach_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["workout_id"] == workout["id"]
    assert body["client_id"] == client_id
    assert body["status"] == "assigned"


def test_coach_assigns_workout_to_nonexistent_user_returns_400(client):
    coach_headers = auth_headers_for_coach(client)
    workout = client.post(
        "/workouts", json={"name": "Leg Day"}, headers=coach_headers
    ).json()

    response = client.post(
        f"/workouts/{workout['id']}/assign",
        json={"client_id": 999999},
        headers=coach_headers,
    )

    assert response.status_code == 400


def test_coach_assigns_workout_to_a_coach_returns_400(client):
    coach_headers = auth_headers_for_coach(client)
    other_coach_headers = auth_headers_for_coach(client, email="other-coach@example.com")
    other_coach_id = get_user_id(client, other_coach_headers)

    workout = client.post(
        "/workouts", json={"name": "Leg Day"}, headers=coach_headers
    ).json()

    response = client.post(
        f"/workouts/{workout['id']}/assign",
        json={"client_id": other_coach_id},
        headers=coach_headers,
    )

    assert response.status_code == 400


def test_coach_assigns_nonexistent_workout_returns_404(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)

    response = client.post(
        "/workouts/999999/assign", json={"client_id": client_id}, headers=coach_headers
    )

    assert response.status_code == 404


def test_coach_cannot_assign_another_coachs_workout(client):
    coach_headers = auth_headers_for_coach(client)
    other_coach_headers = auth_headers_for_coach(client, email="other-coach@example.com")
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)

    workout = client.post(
        "/workouts", json={"name": "Leg Day"}, headers=coach_headers
    ).json()

    response = client.post(
        f"/workouts/{workout['id']}/assign",
        json={"client_id": client_id},
        headers=other_coach_headers,
    )

    assert response.status_code == 404


def test_client_cannot_create_workout_returns_403(client):
    client_headers = auth_headers_for_client(client)

    response = client.post("/workouts", json={"name": "Leg Day"}, headers=client_headers)

    assert response.status_code == 403


def test_coach_lists_only_their_own_workouts(client):
    coach_headers = auth_headers_for_coach(client)
    other_coach_headers = auth_headers_for_coach(client, email="other-coach@example.com")

    client.post("/workouts", json={"name": "Mine"}, headers=coach_headers)
    client.post("/workouts", json={"name": "Not Mine"}, headers=other_coach_headers)

    response = client.get("/workouts", headers=coach_headers)

    assert response.status_code == 200
    names = [w["name"] for w in response.json()]
    assert names == ["Mine"]


def test_create_workout_with_missing_name_returns_422(client):
    coach_headers = auth_headers_for_coach(client)

    response = client.post("/workouts", json={"description": "no name given"}, headers=coach_headers)

    assert response.status_code == 422


def test_coach_lists_assignments_they_have_given_out(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)

    workout = client.post(
        "/workouts", json={"name": "Leg Day"}, headers=coach_headers
    ).json()
    client.post(
        f"/workouts/{workout['id']}/assign", json={"client_id": client_id}, headers=coach_headers
    )

    response = client.get("/assignments", headers=coach_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["client_id"] == client_id


def test_client_lists_only_their_own_assignments(client):
    coach_headers = auth_headers_for_coach(client)
    client_headers = auth_headers_for_client(client)
    client_id = get_user_id(client, client_headers)

    workout = client.post(
        "/workouts", json={"name": "Leg Day"}, headers=coach_headers
    ).json()
    client.post(
        f"/workouts/{workout['id']}/assign", json={"client_id": client_id}, headers=coach_headers
    )

    response = client.get("/assignments", headers=client_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["workout_id"] == workout["id"]
