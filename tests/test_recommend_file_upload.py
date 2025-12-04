"""
Integration-style tests for /api/recommend using file upload.
"""

import io

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


def test_recommend_with_pdf_like_upload() -> None:
    """
    The endpoint should accept a file upload and return a result.

    This test uses a small text payload with a fake PDF content type to
    avoid the need for real binary fixtures.
    """
    job_description = "Fullstack developer working with FastAPI and React."
    dummy_pdf_bytes = b"Sample resume content for integration test."

    files = {
        "resume_file": (
            "resume.pdf",
            io.BytesIO(dummy_pdf_bytes),
            "application/pdf",
        )
    }
    data = {"job_description": job_description}

    response = client.post("/api/recommend", data=data, files=files)
    assert response.status_code == 200

    payload = response.json()
    resumes = payload["resumes"]
    assert resumes, "Expected at least one tailored resume from file upload"

    first = resumes[0]
    assert "Sample resume content" in first["content"]


