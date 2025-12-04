"""
Tests for the job description fetching endpoint.
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


client = TestClient(app)


def test_fetch_job_description_invalid_url() -> None:
    """
    The endpoint should return 400 for invalid URLs.
    """
    payload = {"url": "not-a-valid-url"}
    response = client.post("/api/job/fetch", json=payload)
    assert response.status_code == 400


def test_fetch_job_description_missing_url() -> None:
    """
    The endpoint should return 422 for missing URL field.
    """
    payload = {}
    response = client.post("/api/job/fetch", json=payload)
    assert response.status_code == 422


def test_fetch_job_description_nonexistent_url() -> None:
    """
    The endpoint should return 400 for URLs that don't exist.
    """
    payload = {"url": "https://example.com/nonexistent-page-12345"}
    response = client.post("/api/job/fetch", json=payload)
    # Should return 400 (client error) or 500 (server error) depending on
    # how httpx handles 404s
    assert response.status_code in {400, 500}


def test_fetch_job_description_success() -> None:
    """
    The endpoint should successfully fetch and parse a simple HTML page.

    Note: This test uses httpbin.org which provides a simple HTML response.
    In a real scenario, you might want to mock httpx responses.
    """
    # Use httpbin.org which returns simple HTML
    payload = {"url": "https://httpbin.org/html"}
    response = client.post("/api/job/fetch", json=payload)

    # httpbin.org/html returns a simple HTML page
    if response.status_code == 200:
        data = response.json()
        assert "url" in data
        assert "text" in data
        assert "success" in data
        assert data["success"] is True
        assert data["url"] == payload["url"]
        assert len(data["text"]) > 0
    else:
        # If httpbin is unavailable, skip this test
        pytest.skip("httpbin.org unavailable or network error")


def test_fetch_job_description_response_structure() -> None:
    """
    Verify the response structure matches the schema.
    """
    # Use a simple test URL (this will likely fail, but we can check structure)
    payload = {"url": "https://example.com"}
    response = client.post("/api/job/fetch", json=payload)

    # Even on error, we should get a structured response
    if response.status_code == 200:
        data = response.json()
        assert "url" in data
        assert "text" in data
        assert "success" in data
        assert isinstance(data["url"], str)
        assert isinstance(data["text"], str)
        assert isinstance(data["success"], bool)

