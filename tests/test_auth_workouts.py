"""Test authentication, account seeding, and user-owned workout endpoints."""

import asyncio
from typing import cast

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.security import ALGORITHM
from app.main import app
from app.seed_test_accounts import load_seed_accounts, seed_test_accounts
from tests.fakes import FakeSession


@pytest.fixture
def auth_client(client: TestClient) -> tuple[TestClient, FakeSession]:
    """Override database access with an isolated in-memory session per test."""
    session = FakeSession()

    async def provide_session() -> FakeSession:
        return session

    app.dependency_overrides[get_db_session] = provide_session
    return client, session


def test_registration_creates_regular_user_without_exposing_hash(
    auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, session = auth_client
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "Person@Example.com", "password": "correct-horse-battery"},
    )

    assert response.status_code == 201
    body = response.json()["data"]["user"]
    assert body == {"id": 1, "email": "person@example.com", "role": "user"}
    assert "password_hash" not in response.text
    assert session.users[0].password_hash != "correct-horse-battery"
    assert session.users[0].password_hash.startswith("$argon2")


def test_registration_rejects_duplicate_and_privileged_role(
    auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, _ = auth_client
    payload = {"email": "person@example.com", "password": "correct-horse-battery"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    duplicate = client.post(
        "/api/v1/auth/register",
        json={"email": "PERSON@example.com", "password": "another-secure-password"},
    )
    escalation = client.post(
        "/api/v1/auth/register",
        json={**payload, "role": "superadmin"},
    )

    assert duplicate.status_code == 409
    assert escalation.status_code == 422


def test_registration_rejects_invalid_email_and_short_password(
    auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, _ = auth_client
    invalid_email = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "correct-horse-battery"},
    )
    short_password = client.post(
        "/api/v1/auth/register",
        json={"email": "person@example.com", "password": "short"},
    )

    assert invalid_email.status_code == short_password.status_code == 422


def test_login_returns_token_and_me_requires_valid_token(
    auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        json={"email": "person@example.com", "password": "correct-horse-battery"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "correct-horse-battery"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["token_type"] == "bearer"
    token = response.json()["data"]["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    missing = client.get("/api/v1/auth/me")
    invalid = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token"})

    assert me.status_code == 200
    assert me.json()["data"]["user"]["email"] == "person@example.com"
    assert "password_hash" not in me.text
    assert missing.status_code == invalid.status_code == 401


def test_login_failure_is_generic_and_expired_tokens_are_rejected(
    auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        json={"email": "person@example.com", "password": "correct-horse-battery"},
    )
    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "wrong-password"},
    )
    unknown_email = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )
    settings = get_settings()
    expired_token = jwt.encode(
        {"sub": "1", "type": "access", "exp": 1},
        settings.auth_secret_key,
        algorithm=ALGORITHM,
    )
    expired = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert expired.status_code == 401


def test_workout_endpoints_require_authentication_and_isolate_owners(
    auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, _ = auth_client
    payload_a = {"email": "a@example.com", "password": "correct-horse-battery"}
    payload_b = {"email": "b@example.com", "password": "correct-horse-battery"}
    client.post("/api/v1/auth/register", json=payload_a)
    client.post("/api/v1/auth/register", json=payload_b)
    token_a = client.post("/api/v1/auth/login", json=payload_a).json()["data"]["access_token"]
    token_b = client.post("/api/v1/auth/login", json=payload_b).json()["data"]["access_token"]
    unauthenticated = client.get("/api/v1/workouts")
    created = client.post(
        "/api/v1/workouts",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"workout_data": {"name": "Leg day", "duration_minutes": 45}},
    )
    own_records = client.get("/api/v1/workouts", headers={"Authorization": f"Bearer {token_a}"})
    other_records = client.get("/api/v1/workouts", headers={"Authorization": f"Bearer {token_b}"})

    assert unauthenticated.status_code == 401
    assert created.status_code == 201
    assert created.json()["data"]["workout"]["workout_data"]["name"] == "Leg day"
    assert len(own_records.json()["data"]["workouts"]) == 1
    assert other_records.json()["data"]["workouts"] == []


def test_workout_rejects_invalid_payload(
    auth_client: tuple[TestClient, FakeSession],
) -> None:
    client, _ = auth_client
    client.post(
        "/api/v1/auth/register",
        json={"email": "person@example.com", "password": "correct-horse-battery"},
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "correct-horse-battery"},
    ).json()["data"]["access_token"]
    response = client.post(
        "/api/v1/workouts",
        headers={"Authorization": f"Bearer {token}"},
        json={"workout_data": []},
    )

    assert response.status_code == 422


def test_seeder_creates_each_role_once_and_refuses_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for role, email in (
        ("SUPERADMIN", "root@example.com"),
        ("ADMIN", "admin@example.com"),
        ("USER", "user@example.com"),
    ):
        monkeypatch.setenv(f"SEED_{role}_EMAIL", email)
        monkeypatch.setenv(f"SEED_{role}_PASSWORD", "seed-password-secure")

    session = FakeSession()
    async_session = cast(AsyncSession, session)
    assert asyncio.run(seed_test_accounts(async_session)) == 3
    assert asyncio.run(seed_test_accounts(async_session)) == 0
    assert {user.role for user in session.users} == {"superadmin", "admin", "user"}
    assert all(user.password_hash.startswith("$argon2") for user in session.users)

    monkeypatch.setattr(
        "app.seed_test_accounts.get_settings",
        lambda: Settings(app_env="production", auth_secret_key="s" * 40),
    )
    with pytest.raises(RuntimeError, match="only be seeded"):
        asyncio.run(seed_test_accounts(cast(AsyncSession, FakeSession())))


def test_seeder_rejects_missing_or_duplicate_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.seed_test_accounts.dotenv_values", lambda _: {})
    with pytest.raises(ValueError, match="are required"):
        load_seed_accounts()

    for role in ("SUPERADMIN", "ADMIN", "USER"):
        monkeypatch.setenv(f"SEED_{role}_EMAIL", "same@example.com")
        monkeypatch.setenv(f"SEED_{role}_PASSWORD", "seed-password-secure")
    with pytest.raises(ValueError, match="must be unique"):
        load_seed_accounts()
