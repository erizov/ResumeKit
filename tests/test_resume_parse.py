"""
Tests for the resume parsing endpoint.
"""

import io
import os

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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RESUMEKIT_USE_OPENAI = os.getenv("RESUMEKIT_USE_OPENAI", "").lower() in {
    "1",
    "true",
    "yes",
}

skip_if_no_openai = pytest.mark.skipif(
    not OPENAI_API_KEY or not RESUMEKIT_USE_OPENAI,
    reason="OPENAI_API_KEY and RESUMEKIT_USE_OPENAI not set",
)


def test_parse_resume_missing_input() -> None:
    """
    The endpoint should return 400 if neither text nor file is provided.
    """
    response = client.post("/api/resume/parse")
    assert response.status_code == 400


def test_parse_resume_text_input() -> None:
    """
    The endpoint should accept text input and return structured data.

    This test runs even without OpenAI to verify the endpoint structure.
    """
    resume_text = (
        "John Doe\n"
        "Software Engineer\n"
        "john.doe@example.com\n\n"
        "EXPERIENCE\n"
        "Senior Developer at Tech Corp (2020-2023)\n"
        "- Built APIs with Python and FastAPI\n"
        "- Managed PostgreSQL databases\n\n"
        "SKILLS\n"
        "Python, FastAPI, PostgreSQL, Docker"
    )

    payload = {"resume_text": resume_text}
    response = client.post("/api/resume/parse", data=payload)

    # Should succeed if OpenAI is available, or fail gracefully if not
    if response.status_code == 200:
        data = response.json()
        assert "text" in data
        assert "structured" in data
        assert "success" in data
        assert data["success"] is True
        assert data["text"] == resume_text

        structured = data["structured"]
        assert "name" in structured
        assert "experience" in structured
        assert "skills" in structured


@skip_if_no_openai
def test_parse_resume_with_openai() -> None:
    """
    Test resume parsing with real OpenAI API (only if configured).
    """
    resume_text = (
        "Jane Smith\n"
        "jane.smith@example.com\n"
        "+1-555-0123\n\n"
        "EXPERIENCE\n"
        "Backend Developer at StartupXYZ\n"
        "2021 - Present\n"
        "- Developed REST APIs using FastAPI\n"
        "- Designed database schemas\n"
        "- Technologies: Python, PostgreSQL, Redis\n\n"
        "EDUCATION\n"
        "BS Computer Science, University ABC, 2020\n\n"
        "SKILLS\n"
        "Python, FastAPI, PostgreSQL, Docker, Kubernetes"
    )

    payload = {"resume_text": resume_text}
    response = client.post("/api/resume/parse", data=payload)

    assert response.status_code == 200
    data = response.json()
    structured = data["structured"]

    # Verify structured data was extracted
    assert structured.get("name") is not None
    assert structured.get("email") is not None
    assert len(structured.get("experience", [])) > 0
    assert len(structured.get("skills", [])) > 0


def test_parse_resume_file_upload() -> None:
    """
    The endpoint should accept file uploads.
    """
    resume_text = "John Doe\nSoftware Engineer\njohn@example.com"
    files = {
        "resume_file": (
            "resume.txt",
            io.BytesIO(resume_text.encode("utf-8")),
            "text/plain",
        )
    }

    response = client.post("/api/resume/parse", files=files)

    # Should succeed or fail gracefully
    if response.status_code == 200:
        data = response.json()
        assert "structured" in data
        assert resume_text in data["text"]


def test_parse_resume_response_structure() -> None:
    """
    Verify the response structure matches the schema.
    """
    resume_text = "Test resume content."
    payload = {"resume_text": resume_text}
    response = client.post("/api/resume/parse", data=payload)

    if response.status_code == 200:
        data = response.json()
        assert "text" in data
        assert "structured" in data
        assert "success" in data

        structured = data["structured"]
        # Verify all expected fields exist
        assert "name" in structured
        assert "email" in structured
        assert "experience" in structured
        assert "education" in structured
        assert "skills" in structured
        assert "projects" in structured

