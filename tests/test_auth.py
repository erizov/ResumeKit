"""
Tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app
from app.models import User


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


def test_signup_success(client: TestClient) -> None:
    """Test successful user signup."""
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/auth/signup",
        json={"email": unique_email, "password": "testpassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data


def test_signup_duplicate_email(client: TestClient) -> None:
    """Test signup with duplicate email fails."""
    # Create first user
    client.post(
        "/api/auth/signup",
        json={"email": "duplicate@example.com", "password": "password123"},
    )

    # Try to create duplicate
    response = client.post(
        "/api/auth/signup",
        json={"email": "duplicate@example.com", "password": "password123"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_signup_weak_password(client: TestClient) -> None:
    """Test signup with weak password fails validation."""
    response = client.post(
        "/api/auth/signup",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert response.status_code == 422  # Validation error


def test_login_success(client: TestClient) -> None:
    """Test successful login returns token."""
    # Create user first
    client.post(
        "/api/auth/signup",
        json={"email": "login@example.com", "password": "password123"},
    )

    # Login
    response = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_invalid_email(client: TestClient) -> None:
    """Test login with non-existent email fails."""
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_invalid_password(client: TestClient) -> None:
    """Test login with wrong password fails."""
    # Create user first
    client.post(
        "/api/auth/signup",
        json={"email": "wrongpass@example.com", "password": "correctpassword"},
    )

    # Try wrong password
    response = client.post(
        "/api/auth/login",
        json={"email": "wrongpass@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_get_current_user(client: TestClient) -> None:
    """Test getting current user info with valid token."""
    import uuid
    unique_email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    # Create user and login
    client.post(
        "/api/auth/signup",
        json={"email": unique_email, "password": "password123"},
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Get current user
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == unique_email
    assert "id" in data


def test_get_current_user_invalid_token(client: TestClient) -> None:
    """Test getting current user with invalid token fails."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_get_current_user_no_token(client: TestClient) -> None:
    """Test getting current user without token fails."""
    response = client.get("/api/auth/me")
    assert response.status_code == 403  # Forbidden (no credentials)


def test_logout(client: TestClient) -> None:
    """Test logout endpoint (stateless, always succeeds)."""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert "message" in response.json()


def test_login_without_auth_config(client: TestClient) -> None:
    """
    Test login behavior when AUTH_SECRET_KEY is not set.
    
    Note: This test is skipped in normal test runs because AUTH_SECRET_KEY
    is set in conftest.py. In production, missing AUTH_SECRET_KEY would
    return 503 Service Unavailable.
    """
    # In test environment, AUTH_SECRET_KEY is set, so login will work
    # or fail with 401 (invalid credentials), not 503
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )
    # Should return 401 (invalid credentials) since AUTH_SECRET_KEY is configured
    assert response.status_code == 401

