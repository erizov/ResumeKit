"""
Tests for history and detail endpoints.
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


def _create_sample_tailored_resumes() -> None:
    payload = {
        "job_description": "Backend role using FastAPI.",
        "resume_text": "Developer experienced with FastAPI and SQLAlchemy.",
        "languages": "en,ru",
        "targets": "backend",
    }
    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200


def test_history_returns_items() -> None:
    """
    GET /api/history should return at least one item after tailoring.
    """
    _create_sample_tailored_resumes()

    response = client.get("/api/history?limit=10&offset=0")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= len(data["items"])

    if data["items"]:
        first = data["items"][0]
        assert "id" in first
        assert "language" in first
        assert "target" in first
        assert "created_at" in first


def test_get_tailored_resume_detail() -> None:
    """
    GET /api/tailor/{id} should return detailed information.
    """
    payload = {
        "job_description": "GPT engineer role.",
        "resume_text": "Engineer with GPT and LLM experience.",
        "languages": "en",
        "targets": "gpt_engineer",
    }
    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200

    data = response.json()
    resumes = data["resumes"]
    assert resumes
    resume_id = resumes[0]["id"]

    detail_response = client.get(f"/api/tailor/{resume_id}")
    assert detail_response.status_code == 200

    detail = detail_response.json()
    assert detail["id"] == resume_id
    assert detail["language"] == "en"
    assert detail["target"] == "gpt_engineer"
    assert "Engineer with GPT" in detail["base_resume_text"]
    assert "GPT engineer role" in detail["job_description"]


