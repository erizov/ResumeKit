"""
Tests for keyword coverage analysis.
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


def test_keyword_coverage_endpoint_not_found() -> None:
    """
    Coverage endpoint should return 404 for non-existent resume ID.
    """
    response = client.get("/api/tailor/99999/coverage")
    assert response.status_code == 404


def test_keyword_coverage_basic() -> None:
    """
    Test keyword coverage analysis with a simple resume and JD.
    """
    # Create a tailored resume first
    payload = {
        "job_description": (
            "Backend Developer position. "
            "Required: Python, FastAPI, PostgreSQL, Docker. "
            "Nice to have: Kubernetes, Redis."
        ),
        "resume_text": (
            "Experienced backend developer. "
            "Skills: Python, FastAPI, PostgreSQL, Docker, Git."
        ),
        "languages": "en",
        "targets": "backend",
    }

    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200

    resumes = response.json()["resumes"]
    assert resumes
    resume_id = resumes[0]["id"]

    # Get coverage
    coverage_response = client.get(f"/api/tailor/{resume_id}/coverage")
    assert coverage_response.status_code == 200

    coverage = coverage_response.json()
    assert "matched" in coverage
    assert "missing" in coverage
    assert "score" in coverage
    assert "total_jd_keywords" in coverage
    assert "total_resume_keywords" in coverage

    # Verify matched keywords include expected ones
    matched = coverage["matched"]
    assert "Python" in matched or "python" in matched.lower()
    assert "FastAPI" in matched or "fastapi" in matched

    # Verify score is between 0 and 1
    assert 0.0 <= coverage["score"] <= 1.0


def test_keyword_coverage_high_match() -> None:
    """
    Test coverage when resume matches most JD keywords.
    """
    payload = {
        "job_description": "Python developer with FastAPI and PostgreSQL.",
        "resume_text": "Python developer experienced with FastAPI and PostgreSQL.",
        "languages": "en",
        "targets": "backend",
    }

    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200

    resume_id = response.json()["resumes"][0]["id"]
    coverage_response = client.get(f"/api/tailor/{resume_id}/coverage")
    assert coverage_response.status_code == 200

    coverage = coverage_response.json()
    # Should have high coverage score
    assert coverage["score"] >= 0.5


def test_keyword_coverage_low_match() -> None:
    """
    Test coverage when resume has few matching keywords.
    """
    payload = {
        "job_description": "Java developer with Spring Boot and MongoDB.",
        "resume_text": "Python developer with FastAPI and PostgreSQL.",
        "languages": "en",
        "targets": "backend",
    }

    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200

    resume_id = response.json()["resumes"][0]["id"]
    coverage_response = client.get(f"/api/tailor/{resume_id}/coverage")
    assert coverage_response.status_code == 200

    coverage = coverage_response.json()
    # Should have low coverage score
    assert coverage["score"] < 0.5
    # Should have missing keywords
    assert len(coverage["missing"]) > 0


def test_keyword_coverage_response_structure() -> None:
    """
    Verify coverage response structure matches schema.
    """
    payload = {
        "job_description": "Developer role.",
        "resume_text": "Developer with experience.",
        "languages": "en",
        "targets": "backend",
    }

    response = client.post("/api/recommend", data=payload)
    resume_id = response.json()["resumes"][0]["id"]

    coverage_response = client.get(f"/api/tailor/{resume_id}/coverage")
    assert coverage_response.status_code == 200

    coverage = coverage_response.json()
    assert isinstance(coverage["matched"], list)
    assert isinstance(coverage["missing"], list)
    assert isinstance(coverage["score"], (int, float))
    assert isinstance(coverage["total_jd_keywords"], int)
    assert isinstance(coverage["total_resume_keywords"], int)

