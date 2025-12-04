"""
End-to-end API integration tests for the full ResumeKit workflow.

These tests verify the complete flow from resume upload through
tailoring, history retrieval, and detail viewing.
"""

import io
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture(autouse=True, scope="module")
def _ensure_tables():
    """
    Ensure database tables exist before running API tests.

    This fixture runs once per test module to create tables.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # Tables remain for subsequent tests in the module


client = TestClient(app)


def test_full_workflow_text_resume() -> None:
    """
    Complete workflow: text resume → generate → history → detail.

    This test verifies the entire API flow works end-to-end.
    """
    # Step 1: Generate tailored resumes
    payload = {
        "job_description": (
            "Senior Backend Developer position. "
            "Required: Python, FastAPI, PostgreSQL, Docker. "
            "Nice to have: Kubernetes, Redis."
        ),
        "resume_text": (
            "Experienced backend developer with 5+ years in Python. "
            "Expert in FastAPI, SQLAlchemy, and PostgreSQL. "
            "Familiar with Docker and cloud deployments."
        ),
        "languages": "en,ru",
        "targets": "backend",
        "aggressiveness": 2,
    }

    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200

    data = response.json()
    assert "resumes" in data
    resumes: List[Dict] = data["resumes"]
    assert len(resumes) == 2  # en + ru

    # Verify resume structure
    for resume in resumes:
        assert "id" in resume
        assert "language" in resume
        assert "target" in resume
        assert "content" in resume
        assert "created_at" in resume
        assert resume["language"] in {"en", "ru"}
        assert resume["target"] == "backend"
        assert "Experienced backend developer" in resume["content"]

    # Step 2: Retrieve history
    history_response = client.get("/api/history?limit=10&offset=0")
    assert history_response.status_code == 200

    history_data = history_response.json()
    assert "items" in history_data
    assert "total" in history_data
    assert history_data["total"] >= 2

    # Find our generated resumes in history
    history_items = history_data["items"]
    generated_ids = {r["id"] for r in resumes}
    history_ids = {item["id"] for item in history_items}

    # At least some of our generated resumes should be in history
    assert generated_ids.intersection(history_ids), (
        "Generated resumes should appear in history"
    )

    # Step 3: Get detail for one of the generated resumes
    first_resume_id = resumes[0]["id"]
    detail_response = client.get(f"/api/tailor/{first_resume_id}")
    assert detail_response.status_code == 200

    detail = detail_response.json()
    assert detail["id"] == first_resume_id
    assert detail["language"] == resumes[0]["language"]
    assert detail["target"] == resumes[0]["target"]
    assert "Experienced backend developer" in detail["base_resume_text"]
    assert "Senior Backend Developer" in detail["job_description"]
    assert detail["content"] == resumes[0]["content"]


def test_full_workflow_file_upload() -> None:
    """
    Complete workflow: file upload → generate → history → detail.

    Tests the file upload path through the full flow.
    """
    job_description = "Fullstack developer role with React and FastAPI."
    dummy_resume_text = (
        "Fullstack developer with React, TypeScript, and FastAPI experience. "
        "5 years building web applications."
    )

    files = {
        "resume_file": (
            "resume.txt",
            io.BytesIO(dummy_resume_text.encode("utf-8")),
            "text/plain",
        )
    }
    data = {
        "job_description": job_description,
        "languages": "en",
        "targets": "fullstack",
    }

    # Step 1: Generate via file upload
    response = client.post("/api/recommend", data=data, files=files)
    assert response.status_code == 200

    result = response.json()
    resumes = result["resumes"]
    assert len(resumes) == 1
    assert resumes[0]["language"] == "en"
    assert resumes[0]["target"] == "fullstack"
    assert "Fullstack developer" in resumes[0]["content"]

    resume_id = resumes[0]["id"]

    # Step 2: Verify in history
    history_response = client.get("/api/history")
    assert history_response.status_code == 200
    history = history_response.json()
    history_ids = {item["id"] for item in history["items"]}
    assert resume_id in history_ids

    # Step 3: Get detail
    detail_response = client.get(f"/api/tailor/{resume_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == resume_id
    assert "Fullstack developer" in detail["base_resume_text"]
    assert "Fullstack developer role" in detail["job_description"]


def test_multiple_generations_preserved() -> None:
    """
    Multiple generations should all be preserved and retrievable.

    Tests that generating multiple tailored resumes doesn't lose
    previous ones and all can be retrieved via history.
    """
    # Generate first batch
    payload1 = {
        "job_description": "Backend role.",
        "resume_text": "Backend developer.",
        "languages": "en",
        "targets": "backend",
    }
    response1 = client.post("/api/recommend", data=payload1)
    assert response1.status_code == 200
    batch1_ids = {r["id"] for r in response1.json()["resumes"]}

    # Generate second batch
    payload2 = {
        "job_description": "Frontend role.",
        "resume_text": "Frontend developer.",
        "languages": "ru",
        "targets": "fullstack",
    }
    response2 = client.post("/api/recommend", data=payload2)
    assert response2.status_code == 200
    batch2_ids = {r["id"] for r in response2.json()["resumes"]}

    # Verify both batches are in history
    history_response = client.get("/api/history?limit=100")
    assert history_response.status_code == 200
    history = history_response.json()
    history_ids = {item["id"] for item in history["items"]}

    assert batch1_ids.issubset(history_ids), "Batch 1 should be in history"
    assert batch2_ids.issubset(history_ids), "Batch 2 should be in history"


def test_history_pagination() -> None:
    """
    History endpoint should support pagination correctly.
    """
    # Generate some data
    for i in range(5):
        payload = {
            "job_description": f"Job {i}.",
            "resume_text": f"Resume {i}.",
            "languages": "en",
            "targets": "backend",
        }
        client.post("/api/recommend", data=payload)

    # Test pagination
    page1 = client.get("/api/history?limit=2&offset=0").json()
    page2 = client.get("/api/history?limit=2&offset=2").json()

    assert len(page1["items"]) <= 2
    assert len(page2["items"]) <= 2
    assert page1["total"] == page2["total"]  # Total should be consistent

    # Items should not overlap
    page1_ids = {item["id"] for item in page1["items"]}
    page2_ids = {item["id"] for item in page2["items"]}
    assert not page1_ids.intersection(page2_ids), "Pages should not overlap"


def test_history_filtering() -> None:
    """
    History endpoint should filter by language and target correctly.
    """
    # Generate resumes with different languages/targets
    payload_en_backend = {
        "job_description": "Backend role.",
        "resume_text": "Backend developer.",
        "languages": "en",
        "targets": "backend",
    }
    client.post("/api/recommend", data=payload_en_backend)

    payload_ru_fullstack = {
        "job_description": "Fullstack role.",
        "resume_text": "Fullstack developer.",
        "languages": "ru",
        "targets": "fullstack",
    }
    client.post("/api/recommend", data=payload_ru_fullstack)

    # Filter by language
    en_history = client.get("/api/history?language=en").json()
    assert all(item["language"] == "en" for item in en_history["items"])

    # Filter by target
    backend_history = client.get("/api/history?target=backend").json()
    assert all(item["target"] == "backend" for item in backend_history["items"])

    # Combined filter
    filtered = client.get("/api/history?language=en&target=backend").json()
    assert all(
        item["language"] == "en" and item["target"] == "backend"
        for item in filtered["items"]
    )


def test_error_handling_invalid_resume_id() -> None:
    """
    Detail endpoint should return 404 for non-existent resume ID.
    """
    response = client.get("/api/tailor/99999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_error_handling_missing_required_fields() -> None:
    """
    Recommend endpoint should return 400 for missing required fields.
    """
    # Missing job_description
    response = client.post("/api/recommend", data={"resume_text": "Resume."})
    assert response.status_code == 422  # FastAPI validation error

    # Missing resume
    response = client.post(
        "/api/recommend", data={"job_description": "Job."}
    )
    assert response.status_code == 400


