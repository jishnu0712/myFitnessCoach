"""Test health endpoints and the centralized API error response contract."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db_session
from app.core.exception_handlers import register_exception_handlers
from app.core.exceptions import NotFoundException
from app.main import app


class FakeSession:
    """Minimal async session stand-in that avoids requiring PostgreSQL in tests."""

    def __init__(self, should_fail: bool = False) -> None:
        """Choose whether the fake query succeeds or raises a database error."""
        self.should_fail = should_fail

    async def execute(self, statement: object) -> None:
        """Pretend to execute the health query or simulate a database outage."""
        del statement
        if self.should_fail:
            raise SQLAlchemyError("simulated database failure")


def override_database(session: FakeSession) -> None:
    """Override the request database dependency with a fake session."""

    async def provide_session() -> FakeSession:
        """Return the configured fake session through dependency injection."""
        return session

    app.dependency_overrides[get_db_session] = provide_session


def test_health_endpoint_returns_success_envelope(client: TestClient) -> None:
    """The process liveness endpoint responds without needing a database."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"status": "healthy"}}


def test_database_health_endpoint_returns_success(client: TestClient) -> None:
    """The readiness endpoint returns healthy when its query succeeds."""
    override_database(FakeSession())

    response = client.get("/api/v1/health/db")

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"status": "healthy"}}


def test_database_health_endpoint_returns_safe_503(client: TestClient) -> None:
    """A database outage maps to 503 without leaking the driver error message."""
    override_database(FakeSession(should_fail=True))

    response = client.get("/api/v1/health/db")

    assert response.status_code == 503
    assert response.json() == {
        "success": False,
        "error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "Database is unavailable",
            "details": None,
        },
    }
    assert "simulated database failure" not in response.text


def test_http_404_uses_error_envelope(client: TestClient) -> None:
    """Framework 404 responses follow the same public JSON error contract."""
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "error": {
            "code": "HTTP_ERROR",
            "message": "Not Found",
            "details": None,
        },
    }


def test_application_exception_uses_error_envelope() -> None:
    """Known application errors preserve their status and stable public code."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/missing")
    async def missing_resource() -> None:
        """Raise a representative feature-level not-found exception."""
        raise NotFoundException("Workout plan not found")

    with TestClient(test_app) as test_client:
        response = test_client.get("/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_request_validation_uses_error_envelope() -> None:
    """Request validation reports the field but never echoes supplied input."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/items/{item_id}")
    async def read_item(item_id: int) -> dict[str, int]:
        """Return an integer path value after FastAPI validates its type."""
        return {"item_id": item_id}

    with TestClient(test_app) as test_client:
        response = test_client.get("/items/not-an-integer")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "not-an-integer" not in response.text


def test_unexpected_error_does_not_expose_exception_details() -> None:
    """Unexpected implementation errors are logged but sanitized for API clients."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/failure")
    async def fail() -> None:
        """Raise a representative unexpected internal error."""
        raise RuntimeError("private implementation detail")

    with TestClient(test_app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/failure")

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": None,
        },
    }
    assert "private implementation detail" not in response.text
