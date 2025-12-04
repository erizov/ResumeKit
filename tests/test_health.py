"""
Tests for health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture(autouse=True, scope="module")
def _ensure_tables():
    """
    Ensure database tables exist before running tests.
    """
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    """
    Test client fixture.
    """
    return TestClient(app)


def test_health_check_healthy(client: TestClient) -> None:
    """Test health check returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_check_endpoint_exists(client: TestClient) -> None:
    """Test health endpoint is accessible."""
    response = client.get("/health")
    assert response.status_code == 200

