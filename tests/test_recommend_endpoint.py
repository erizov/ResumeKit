"""
Tests for the /api/recommend endpoint.
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


def test_recommend_with_text_resume_default_options() -> None:
    """
    The endpoint should return at least one tailored resume when called
    with resume text and a job description.
    """
    payload = {
        "job_description": "Backend developer position working with Python.",
        "resume_text": "Experienced developer with FastAPI and PostgreSQL.",
    }

    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200

    data = response.json()
    assert "resumes" in data
    assert isinstance(data["resumes"], list)
    assert data["resumes"], "Expected at least one tailored resume"

    first = data["resumes"][0]
    assert first["language"] in {"en", "ru"}
    assert first["target"] == "backend"
    assert "Experienced developer" in first["content"]


def test_recommend_requires_resume() -> None:
    """
    The endpoint should reject requests without any resume input.
    """
    payload = {
        "job_description": "Some job.",
    }

    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 400

    data = response.json()
    assert data["detail"].startswith("Either resume_text or resume_file")


def test_recommend_multiple_languages_and_targets() -> None:
    """
    The endpoint should honor comma-separated languages and targets.
    """
    payload = {
        "job_description": "GPT engineer role.",
        "resume_text": "Engineer with LLM and GPT experience.",
        "languages": "en,ru",
        "targets": "backend,gpt_engineer",
    }
    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200

    data = response.json()
    resumes = data["resumes"]
    assert len(resumes) == 4

    langs = {r["language"] for r in resumes}
    targets = {r["target"] for r in resumes}
    assert langs == {"en", "ru"}
    assert targets == {"backend", "gpt_engineer"}


