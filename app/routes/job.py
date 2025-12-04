"""
Job description fetching endpoints.

Provides endpoints for fetching and parsing job descriptions from URLs.
"""

from fastapi import APIRouter, HTTPException

from ..schemas import JobFetchRequest, JobFetchResponse
from ..services.job_parser import fetch_job_description_from_url


router = APIRouter()


@router.post("/fetch", response_model=JobFetchResponse)
async def fetch_job_description(request: JobFetchRequest) -> JobFetchResponse:
    """
    Fetch and parse a job description from a URL.

    The endpoint fetches the HTML content from the provided URL,
    extracts the main text content (removing boilerplate like
    navigation and headers), and returns the plain text job description.

    Example:
        POST /api/job/fetch
        {
            "url": "https://example.com/jobs/backend-developer"
        }
    """
    try:
        text = await fetch_job_description_from_url(request.url)
        return JobFetchResponse(url=request.url, text=text, success=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while fetching job description: {exc}",
        ) from exc

