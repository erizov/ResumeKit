"""
Tests for cover letter generation endpoints.
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


def test_generate_cover_letter_not_found() -> None:
    """
    Cover letter generation should return 404 for non-existent resume ID.
    """
    response = client.post(
        "/api/tailor/99999/cover-letter",
        json={"custom_instructions": None},
    )
    assert response.status_code == 404


def test_generate_cover_letter_requires_openai() -> None:
    """
    Cover letter generation should fail if OpenAI is not enabled.
    """
    # Create a tailored resume first
    payload = {
        "job_description": "Backend developer position.",
        "resume_text": "John Doe\nSoftware Engineer",
        "languages": "en",
        "targets": "backend",
    }

    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200

    resumes = response.json()["resumes"]
    assert resumes
    resume_id = resumes[0]["id"]

    # Try to generate cover letter (should fail without OpenAI)
    cover_letter_response = client.post(
        f"/api/tailor/{resume_id}/cover-letter",
        json={"custom_instructions": None},
    )
    assert cover_letter_response.status_code == 400
    assert "OpenAI" in cover_letter_response.json()["detail"]


def test_get_cover_letter_not_found() -> None:
    """
    Getting cover letter should return 404 if none exists.
    """
    # Create a tailored resume first
    payload = {
        "job_description": "Backend developer position.",
        "resume_text": "John Doe\nSoftware Engineer",
        "languages": "en",
        "targets": "backend",
    }

    response = client.post("/api/recommend", data=payload)
    resume_id = response.json()["resumes"][0]["id"]

    # Try to get cover letter (should fail - none exists)
    cover_letter_response = client.get(f"/api/tailor/{resume_id}/cover-letter")
    assert cover_letter_response.status_code == 404


def test_cover_letter_endpoints_structure() -> None:
    """
    Verify cover letter endpoints exist and have correct structure.
    """
    # Test POST endpoint exists (will fail without OpenAI, but endpoint exists)
    response = client.post(
        "/api/tailor/1/cover-letter",
        json={"custom_instructions": None},
    )
    # Should be 404 (resume not found) or 400 (OpenAI not enabled), not 405 (method not allowed)
    assert response.status_code in {404, 400}

    # Test GET endpoint exists
    response = client.get("/api/tailor/1/cover-letter")
    # Should be 404 (resume not found), not 405 (method not allowed)
    assert response.status_code == 404


