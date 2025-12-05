"""
Tests for cover letter PDF generation.
"""

import pytest

from app.services.cover_letter_pdf_generator import generate_cover_letter_pdf


class TestCoverLetterPDF:
    """Test cover letter PDF generation."""

    @pytest.mark.timeout(5)
    def test_generate_cover_letter_pdf_basic(self) -> None:
        """Test basic PDF generation from cover letter text."""
        cover_letter_text = """Dear Hiring Manager,

I am writing to express my interest in the Backend Developer position.

I have 5 years of experience with Python and FastAPI.

Best regards,
John Doe"""

        pdf_bytes = generate_cover_letter_pdf(cover_letter_text)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")  # PDF file signature

    @pytest.mark.timeout(5)
    def test_generate_cover_letter_pdf_russian(self) -> None:
        """Test PDF generation for Russian cover letter."""
        cover_letter_text = """Уважаемые господа,

Меня заинтересовала вакансия Backend-разработчика.

У меня 10 лет опыта работы с Python и Java.

С уважением,
Иван Иванов"""

        pdf_bytes = generate_cover_letter_pdf(cover_letter_text)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    @pytest.mark.timeout(5)
    def test_generate_cover_letter_pdf_empty(self) -> None:
        """Test PDF generation with empty text (should still generate PDF)."""
        pdf_bytes = generate_cover_letter_pdf("")
        # Empty text should still generate a valid PDF (just empty)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    @pytest.mark.timeout(5)
    def test_generate_cover_letter_pdf_multiple_paragraphs(self) -> None:
        """Test PDF generation with multiple paragraphs."""
        cover_letter_text = """Dear Team,

First paragraph with some content.

Second paragraph with more details.

Third paragraph with closing thoughts.

Sincerely,
Jane Smith"""

        pdf_bytes = generate_cover_letter_pdf(cover_letter_text)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")


class TestCoverLetterPDFAPI:
    """Test cover letter PDF API endpoints."""

    @pytest.mark.timeout(10)
    def test_cover_letter_pdf_endpoint_not_found(self) -> None:
        """Test PDF endpoint with non-existent cover letter."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        response = client.get("/api/cover-letter/99999/pdf")

        assert response.status_code == 404

    @pytest.mark.timeout(10)
    def test_cover_letter_pdf_endpoint_success(self) -> None:
        """Test successful PDF generation via API."""
        from app.main import app
        from app.db import SessionLocal
        from app.models import TailoredResume, TailoredCoverLetter, BaseResume, JobPosting
        from fastapi.testclient import TestClient

        client = TestClient(app)
        db = SessionLocal()

        try:
            # Create test data
            base_resume = BaseResume(text="Test resume")
            job_posting = JobPosting(text="Test job")
            db.add(base_resume)
            db.add(job_posting)
            db.flush()

            tailored_resume = TailoredResume(
                base_resume_id=base_resume.id,
                job_posting_id=job_posting.id,
                language="en",
                target="backend",
                content="Test tailored resume",
            )
            db.add(tailored_resume)
            db.flush()

            cover_letter = TailoredCoverLetter(
                tailored_resume_id=tailored_resume.id,
                text="Test cover letter content",
                version=1,
            )
            db.add(cover_letter)
            db.commit()
            db.refresh(cover_letter)

            # Test PDF endpoint
            response = client.get(f"/api/cover-letter/{cover_letter.id}/pdf")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert len(response.content) > 0
            assert response.content.startswith(b"%PDF")
            assert f"cover_letter_{cover_letter.id}" in response.headers.get(
                "content-disposition", ""
            )
        finally:
            db.close()

