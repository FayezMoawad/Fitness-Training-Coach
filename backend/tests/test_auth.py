"""Integration tests for signup, login, and the /auth/me protected route."""

from datetime import timedelta

import jwt

from app.core.security import create_access_token
from app.models.user import User


def signup_payload(**overrides):
    payload = {
        "email": "coach@example.com",
        "password": "supersecret1",
        "full_name": "Coach One",
        "role": "coach",
    }
    payload.update(overrides)
    return payload


def test_signup_valid_coach_returns_201_without_password(client):
    response = client.post("/auth/signup", json=signup_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "coach@example.com"
    assert body["role"] == "coach"
    assert "password" not in body
    assert "hashed_password" not in body


def test_signup_duplicate_email_returns_409_and_no_duplicate_row(client, db_session):
    first = client.post("/auth/signup", json=signup_payload())
    assert first.status_code == 201

    second = client.post("/auth/signup", json=signup_payload(full_name="Someone Else"))
    assert second.status_code == 409

    count = db_session.query(User).filter(User.email == "coach@example.com").count()
    assert count == 1


def test_signup_malformed_email_returns_422(client):
    response = client.post("/auth/signup", json=signup_payload(email="not-an-email"))
    assert response.status_code == 422


def test_signup_short_password_returns_422(client):
    response = client.post("/auth/signup", json=signup_payload(password="short"))
    assert response.status_code == 422


def test_login_correct_credentials_returns_valid_token(client):
    signup_response = client.post("/auth/signup", json=signup_payload())
    user_id = signup_response.json()["id"]

    response = client.post(
        "/auth/login", json={"email": "coach@example.com", "password": "supersecret1"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"

    from app.core.config import settings

    decoded = jwt.decode(body["access_token"], settings.jwt_secret, algorithms=["HS256"])
    assert decoded["sub"] == str(user_id)
    assert decoded["role"] == "coach"


def test_login_wrong_password_returns_401(client):
    client.post("/auth/signup", json=signup_payload())

    response = client.post(
        "/auth/login", json={"email": "coach@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_nonexistent_email_returns_401(client):
    response = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "supersecret1"}
    )
    assert response.status_code == 401


def test_login_missing_password_returns_422(client):
    response = client.post("/auth/login", json={"email": "coach@example.com"})
    assert response.status_code == 422


def test_signup_missing_role_returns_422(client):
    response = client.post(
        "/auth/signup",
        json={"email": "coach@example.com", "password": "supersecret1", "full_name": "Coach"},
    )
    assert response.status_code == 422


def test_protected_route_without_token_returns_401(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_protected_route_with_tampered_token_returns_401(client):
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_protected_route_with_expired_token_returns_401(client):
    signup_response = client.post("/auth/signup", json=signup_payload())
    user_id = signup_response.json()["id"]

    expired_token = create_access_token(
        subject=str(user_id), role="coach", expires_delta=timedelta(minutes=-5)
    )

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401


def test_protected_route_with_valid_token_returns_current_user(client):
    client.post("/auth/signup", json=signup_payload())
    login_response = client.post(
        "/auth/login", json={"email": "coach@example.com", "password": "supersecret1"}
    )
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "coach@example.com"


def test_password_stored_as_bcrypt_hash_not_plaintext(client, db_session):
    client.post("/auth/signup", json=signup_payload())

    user = db_session.query(User).filter(User.email == "coach@example.com").one()
    assert user.hashed_password != "supersecret1"
    assert user.hashed_password.startswith("$2b$")
