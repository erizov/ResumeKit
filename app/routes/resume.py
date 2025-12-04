"""
Resume parsing endpoints.

Provides endpoints for parsing resumes into structured format.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..schemas import ResumeParseResponse, StructuredResume
from ..services.llm_client import parse_resume_to_structured
from ..services.resume_parser import extract_text_from_upload


router = APIRouter()


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    resume_text: str | None = Form(None),
    resume_file: UploadFile | None = File(None),
) -> ResumeParseResponse:
    """
    Parse a resume into structured format.

    Accepts either raw resume text or an uploaded file (DOCX/PDF).
    Uses OpenAI to extract structured data including:
    - Contact information (name, email, phone, location)
    - Experience entries (title, company, dates, descriptions, technologies)
    - Education entries
    - Skills list
    - Projects

    Example:
        POST /api/resume/parse
        Form data:
        - resume_text: "John Doe\nSoftware Engineer..."
        OR
        - resume_file: (file upload)

    Returns:
        Structured resume data in JSON format.
    """
    if not resume_text and not resume_file:
        raise HTTPException(
            status_code=400,
            detail="Either resume_text or resume_file must be provided.",
        )

    try:
        if resume_file and not resume_text:
            text = await extract_text_from_upload(resume_file)
        else:
            assert resume_text is not None
            text = resume_text

        structured = parse_resume_to_structured(text)

        return ResumeParseResponse(text=text, structured=structured, success=True)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing resume: {exc}",
        ) from exc

