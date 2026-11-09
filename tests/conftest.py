"""Provide isolated FastAPI clients and lightweight database doubles for tests."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Yield a test client and clear dependency overrides after each test."""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
