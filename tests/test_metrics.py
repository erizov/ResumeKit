"""
Tests for metrics endpoint.
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


def test_metrics_endpoint() -> None:
    """
    Metrics endpoint should return basic statistics.
    """
    response = client.get("/api/metrics")
    assert response.status_code == 200

    data = response.json()
    assert "total_base_resumes" in data
    assert "total_job_postings" in data
    assert "total_tailored_resumes" in data
    assert "total_cover_letters" in data

    # All should be integers >= 0
    assert isinstance(data["total_base_resumes"], int)
    assert isinstance(data["total_job_postings"], int)
    assert isinstance(data["total_tailored_resumes"], int)
    assert isinstance(data["total_cover_letters"], int)

    assert data["total_base_resumes"] >= 0
    assert data["total_job_postings"] >= 0
    assert data["total_tailored_resumes"] >= 0
    assert data["total_cover_letters"] >= 0


def test_metrics_after_creating_resume() -> None:
    """
    Metrics should reflect created resumes.
    """
    # Get initial counts
    initial_response = client.get("/api/metrics")
    initial_data = initial_response.json()
    initial_resumes = initial_data["total_tailored_resumes"]

    # Create a tailored resume
    payload = {
        "job_description": "Backend developer position.",
        "resume_text": "John Doe\nSoftware Engineer",
        "languages": "en",
        "targets": "backend",
    }

    client.post("/api/recommend", data=payload)

    # Check metrics again
    updated_response = client.get("/api/metrics")
    updated_data = updated_response.json()

    assert updated_data["total_tailored_resumes"] > initial_resumes


