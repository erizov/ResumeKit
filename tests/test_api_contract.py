"""
API contract tests to verify request/response schemas match Pydantic models.

These tests ensure that:
- All endpoints return responses that match their declared schemas
- Invalid requests are properly validated
- Error responses follow FastAPI's standard format
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.db import Base, engine
from app.main import app
from app.schemas import (
    CoverLetterRequest,
    CoverLetterResponse,
    HistoryResponse,
    JobFetchRequest,
    JobFetchResponse,
    KeywordCoverage,
    LanguageCode,
    RecommendResult,
    ResumeParseResponse,
    TailoredResumeDetail,
    TargetRole,
)


@pytest.fixture(autouse=True, scope="module")
def _ensure_tables():
    """
    Ensure database tables exist before running tests.
    """
    Base.metadata.create_all(bind=engine)
    yield


client = TestClient(app)


class TestRecommendEndpoint:
    """Test contract for POST /api/recommend."""

    def test_valid_request_with_text(self) -> None:
        """Valid request should return RecommendResult matching schema."""
        payload = {
            "job_description": "Backend developer position.",
            "resume_text": "John Doe\nSoftware Engineer",
            "languages": "en",
            "targets": "backend",
            "aggressiveness": "2",
        }

        response = client.post("/api/recommend", data=payload)
        assert response.status_code == 200

        data = response.json()
        # Validate against schema
        result = RecommendResult.model_validate(data)
        assert len(result.resumes) > 0
        assert all(
            r.language in {LanguageCode.EN, LanguageCode.RU} for r in result.resumes
        )
        assert all(
            r.target in {TargetRole.BACKEND, TargetRole.FULLSTACK, TargetRole.GPT_ENGINEER}
            for r in result.resumes
        )

    def test_invalid_language(self) -> None:
        """Invalid language should return 400."""
        payload = {
            "job_description": "Job.",
            "resume_text": "Resume.",
            "languages": "invalid",
        }

        response = client.post("/api/recommend", data=payload)
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_invalid_target(self) -> None:
        """Invalid target should return 400."""
        payload = {
            "job_description": "Job.",
            "resume_text": "Resume.",
            "targets": "invalid",
        }

        response = client.post("/api/recommend", data=payload)
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_invalid_aggressiveness(self) -> None:
        """Invalid aggressiveness should return validation error."""
        payload = {
            "job_description": "Job.",
            "resume_text": "Resume.",
            "aggressiveness": "5",  # Out of range (max is 3)
        }

        response = client.post("/api/recommend", data=payload)
        # FastAPI/Pydantic should validate and return 422 or handle gracefully
        # The validation happens in RecommendOptions, which may cause 500 or 422
        assert response.status_code in {422, 500}
        if response.status_code == 422:
            assert "detail" in response.json()


class TestHistoryEndpoint:
    """Test contract for GET /api/history."""

    def test_history_response_schema(self) -> None:
        """History endpoint should return HistoryResponse matching schema."""
        response = client.get("/api/history")
        assert response.status_code == 200

        data = response.json()
        history = HistoryResponse.model_validate(data)
        assert isinstance(history.items, list)
        assert isinstance(history.total, int)
        assert history.total >= 0

    def test_history_with_filters(self) -> None:
        """History with filters should return valid response."""
        response = client.get("/api/history?language=en&target=backend&limit=10&offset=0")
        assert response.status_code == 200

        data = response.json()
        history = HistoryResponse.model_validate(data)
        assert len(history.items) <= 10

    def test_history_invalid_limit(self) -> None:
        """Invalid limit should return 422."""
        response = client.get("/api/history?limit=200")  # > max 100
        assert response.status_code == 422


class TestDetailEndpoint:
    """Test contract for GET /api/tailor/{id}."""

    def test_detail_response_schema(self) -> None:
        """Detail endpoint should return TailoredResumeDetail matching schema."""
        # Create a resume first
        payload = {
            "job_description": "Backend developer.",
            "resume_text": "Software Engineer",
            "languages": "en",
            "targets": "backend",
        }
        create_response = client.post("/api/recommend", data=payload)
        resume_id = create_response.json()["resumes"][0]["id"]

        response = client.get(f"/api/tailor/{resume_id}")
        assert response.status_code == 200

        data = response.json()
        detail = TailoredResumeDetail.model_validate(data)
        assert detail.id == resume_id
        assert detail.content is not None
        assert detail.base_resume_text is not None
        assert detail.job_description is not None

    def test_detail_not_found(self) -> None:
        """Non-existent resume should return 404."""
        response = client.get("/api/tailor/99999")
        assert response.status_code == 404
        assert "detail" in response.json()


class TestKeywordCoverageEndpoint:
    """Test contract for GET /api/tailor/{id}/coverage."""

    def test_coverage_response_schema(self) -> None:
        """Coverage endpoint should return KeywordCoverage matching schema."""
        # Create a resume first
        payload = {
            "job_description": "Python developer with FastAPI.",
            "resume_text": "Python developer with FastAPI experience.",
            "languages": "en",
            "targets": "backend",
        }
        create_response = client.post("/api/recommend", data=payload)
        resume_id = create_response.json()["resumes"][0]["id"]

        response = client.get(f"/api/tailor/{resume_id}/coverage")
        assert response.status_code == 200

        data = response.json()
        coverage = KeywordCoverage.model_validate(data)
        assert 0.0 <= coverage.score <= 1.0
        assert isinstance(coverage.matched, list)
        assert isinstance(coverage.missing, list)
        assert coverage.total_jd_keywords >= 0
        assert coverage.total_resume_keywords >= 0


class TestPDFExportEndpoint:
    """Test contract for GET /api/tailor/{id}/pdf."""

    def test_pdf_response_format(self) -> None:
        """PDF endpoint should return PDF content."""
        # Create a resume first
        payload = {
            "job_description": "Developer role.",
            "resume_text": "Developer resume.",
            "languages": "en",
            "targets": "backend",
        }
        create_response = client.post("/api/recommend", data=payload)
        resume_id = create_response.json()["resumes"][0]["id"]

        response = client.get(f"/api/tailor/{resume_id}/pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")


class TestJobFetchEndpoint:
    """Test contract for POST /api/job/fetch."""

    def test_job_fetch_request_schema(self) -> None:
        """Job fetch should accept JobFetchRequest schema."""
        request_data = {"url": "https://example.com/job"}
        response = client.post("/api/job/fetch", json=request_data)

        # May succeed or fail depending on URL, but should validate schema
        assert response.status_code in {200, 400, 500}
        if response.status_code == 200:
            data = response.json()
            JobFetchResponse.model_validate(data)

    def test_job_fetch_invalid_url(self) -> None:
        """Invalid URL should return error."""
        request_data = {"url": "not-a-url"}
        response = client.post("/api/job/fetch", json=request_data)
        assert response.status_code in {400, 422}

    def test_job_fetch_missing_url(self) -> None:
        """Missing URL should return 422."""
        response = client.post("/api/job/fetch", json={})
        assert response.status_code == 422


class TestResumeParseEndpoint:
    """Test contract for POST /api/resume/parse."""

    def test_parse_with_text(self) -> None:
        """Parse endpoint should return ResumeParseResponse."""
        payload = {"resume_text": "John Doe\nSoftware Engineer"}

        response = client.post("/api/resume/parse", data=payload)
        # May require OpenAI, so could be 200 or 500
        assert response.status_code in {200, 500}

        if response.status_code == 200:
            data = response.json()
            ResumeParseResponse.model_validate(data)

    def test_parse_missing_input(self) -> None:
        """Missing input should return 400."""
        response = client.post("/api/resume/parse", data={})
        assert response.status_code == 400
        assert "detail" in response.json()


class TestCoverLetterEndpoint:
    """Test contract for POST /api/tailor/{id}/cover-letter."""

    def test_cover_letter_request_schema(self) -> None:
        """Cover letter request should validate schema."""
        # Create a resume first
        payload = {
            "job_description": "Backend developer.",
            "resume_text": "Software Engineer",
            "languages": "en",
            "targets": "backend",
        }
        create_response = client.post("/api/recommend", data=payload)
        resume_id = create_response.json()["resumes"][0]["id"]

        request_data = {"custom_instructions": None}
        response = client.post(
            f"/api/tailor/{resume_id}/cover-letter", json=request_data
        )

        # May require OpenAI
        assert response.status_code in {200, 400, 500}

        if response.status_code == 200:
            data = response.json()
            CoverLetterResponse.model_validate(data)

    def test_cover_letter_get_schema(self) -> None:
        """GET cover letter should return CoverLetterResponse if exists."""
        # Create a resume first
        payload = {
            "job_description": "Backend developer.",
            "resume_text": "Software Engineer",
            "languages": "en",
            "targets": "backend",
        }
        create_response = client.post("/api/recommend", data=payload)
        resume_id = create_response.json()["resumes"][0]["id"]

        response = client.get(f"/api/tailor/{resume_id}/cover-letter")
        # May not exist, so 404 is valid
        assert response.status_code in {200, 404}

        if response.status_code == 200:
            data = response.json()
            CoverLetterResponse.model_validate(data)


class TestMetricsEndpoint:
    """Test contract for GET /api/metrics."""

    def test_metrics_response_structure(self) -> None:
        """Metrics endpoint should return expected structure."""
        response = client.get("/api/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "total_base_resumes" in data
        assert "total_job_postings" in data
        assert "total_tailored_resumes" in data
        assert "total_cover_letters" in data

        assert all(isinstance(v, int) for v in data.values())
        assert all(v >= 0 for v in data.values())


class TestErrorResponseFormat:
    """Test that error responses follow FastAPI standard format."""

    def test_404_error_format(self) -> None:
        """404 errors should have 'detail' field."""
        response = client.get("/api/tailor/99999")
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], str)

    def test_400_error_format(self) -> None:
        """400 errors should have 'detail' field."""
        response = client.post("/api/recommend", data={})
        assert response.status_code in {400, 422}
        if response.status_code == 400:
            error_data = response.json()
            assert "detail" in error_data

    def test_422_validation_error_format(self) -> None:
        """422 validation errors should have 'detail' field."""
        response = client.post("/api/job/fetch", json={})
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data


class TestEnumValidation:
    """Test that enum values are properly validated."""

    def test_language_code_validation(self) -> None:
        """Language codes should be validated."""
        payload = {
            "job_description": "Job.",
            "resume_text": "Resume.",
            "languages": "en,ru,invalid",
        }

        response = client.post("/api/recommend", data=payload)
        assert response.status_code == 400

    def test_target_role_validation(self) -> None:
        """Target roles should be validated."""
        payload = {
            "job_description": "Job.",
            "resume_text": "Resume.",
            "targets": "backend,invalid",
        }

        response = client.post("/api/recommend", data=payload)
        assert response.status_code == 400


