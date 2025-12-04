"""
Tests for PDF export functionality.
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


def test_pdf_export_not_found() -> None:
    """
    PDF export endpoint should return 404 for non-existent resume ID.
    """
    response = client.get("/api/tailor/99999/pdf")
    assert response.status_code == 404


def test_pdf_export_success() -> None:
    """
    PDF export should generate a valid PDF file.
    """
    # Create a tailored resume first
    payload = {
        "job_description": "Backend developer position.",
        "resume_text": (
            "John Doe\n"
            "Software Engineer\n"
            "john.doe@example.com\n\n"
            "EXPERIENCE\n"
            "Senior Developer at Tech Corp\n"
            "- Built APIs with Python\n"
            "- Managed databases\n\n"
            "SKILLS\n"
            "Python, FastAPI, PostgreSQL"
        ),
        "languages": "en",
        "targets": "backend",
    }

    response = client.post("/api/recommend", data=payload)
    assert response.status_code == 200

    resumes = response.json()["resumes"]
    assert resumes
    resume_id = resumes[0]["id"]

    # Export PDF
    pdf_response = client.get(f"/api/tailor/{resume_id}/pdf")
    assert pdf_response.status_code == 200

    # Verify PDF content type
    assert pdf_response.headers["content-type"] == "application/pdf"

    # Verify PDF content (PDF files start with %PDF)
    pdf_content = pdf_response.content
    assert pdf_content.startswith(b"%PDF")

    # Verify content disposition header
    assert "attachment" in pdf_response.headers.get("content-disposition", "")


def test_pdf_export_content() -> None:
    """
    PDF should contain the resume content.
    """
    resume_text = (
        "Jane Smith\n"
        "jane.smith@example.com\n\n"
        "EXPERIENCE\n"
        "Developer at Company XYZ"
    )

    payload = {
        "job_description": "Developer role.",
        "resume_text": resume_text,
        "languages": "en",
        "targets": "backend",
    }

    response = client.post("/api/recommend", data=payload)
    resume_id = response.json()["resumes"][0]["id"]

    pdf_response = client.get(f"/api/tailor/{resume_id}/pdf")
    assert pdf_response.status_code == 200

    # PDF should be non-empty
    assert len(pdf_response.content) > 1000  # PDFs are typically > 1KB


def test_pdf_export_filename() -> None:
    """
    PDF response should include appropriate filename in headers.
    """
    payload = {
        "job_description": "Role.",
        "resume_text": "Resume content.",
        "languages": "en",
        "targets": "backend",
    }

    response = client.post("/api/recommend", data=payload)
    resume_id = response.json()["resumes"][0]["id"]

    pdf_response = client.get(f"/api/tailor/{resume_id}/pdf")
    assert pdf_response.status_code == 200

    content_disposition = pdf_response.headers.get("content-disposition", "")
    assert "resume_" in content_disposition
    assert ".pdf" in content_disposition
    assert str(resume_id) in content_disposition

