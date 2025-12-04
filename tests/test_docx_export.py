"""
Tests for DOCX export endpoint.
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


@pytest.fixture
def client():
    """
    Test client fixture.
    """
    return TestClient(app)


def test_docx_export_success(client: TestClient) -> None:
    """Test successful DOCX export."""
    # First create a tailored resume
    response = client.post(
        "/api/recommend",
        data={
            "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
            "job_description": "Looking for a backend developer",
            "languages": "en",
            "targets": "backend",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert "resumes" in result
    assert len(result["resumes"]) > 0

    resume_id = result["resumes"][0]["id"]

    # Download as DOCX
    docx_response = client.get(f"/api/tailor/{resume_id}/docx")
    assert docx_response.status_code == 200
    assert docx_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )
    assert len(docx_response.content) > 0

    # Verify filename in Content-Disposition header
    assert "attachment" in docx_response.headers["Content-Disposition"]
    assert ".docx" in docx_response.headers["Content-Disposition"]


def test_docx_export_not_found(client: TestClient) -> None:
    """Test DOCX export for non-existent resume."""
    response = client.get("/api/tailor/99999/docx")
    assert response.status_code == 404

