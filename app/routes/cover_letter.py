"""
Cover letter generation endpoints.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..config import RATE_LIMIT_ENABLED
from ..db import get_db
from ..models import TailoredResume, TailoredCoverLetter
from ..schemas import (
    CoverLetterRequest,
    CoverLetterResponse,
    CoverLetterListResponse,
    LanguageCode,
)
from ..services.llm_client import generate_cover_letter_llm
from ..services.cover_letter_pdf_generator import generate_cover_letter_pdf

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


def _apply_rate_limit(func):
    """
    Conditionally apply rate limiting based on configuration.
    """
    if RATE_LIMIT_ENABLED:
        return limiter.limit("5/hour")(func)
    return func


@router.post(
    "/tailor/{resume_id}/cover-letter",
    response_model=CoverLetterListResponse,
)
@_apply_rate_limit
def generate_cover_letter(
    request: Request,
    resume_id: int,
    cover_letter_request: CoverLetterRequest,
    db: Session = Depends(get_db),
) -> CoverLetterListResponse:
    """
    Generate two versions of cover letters for a specific tailored resume.

    Uses OpenAI to generate two different styles of cover letters:
    - Version 1: Traditional, formal style
    - Version 2: Modern, results-oriented style

    Both are based on the tailored resume content and the original job
    description.
    """
    tailored_resume = db.get(TailoredResume, resume_id)
    if tailored_resume is None:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    use_llm = os.getenv("RESUMEKIT_USE_OPENAI", "").lower() in {"1", "true", "yes"}

    if not use_llm:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cover letter generation requires OpenAI. "
                "Set RESUMEKIT_USE_OPENAI=1 and configure OPENAI_API_KEY."
            ),
        )

    # Get job description from the related job posting
    job_posting = tailored_resume.job_posting
    if job_posting is None:
        raise HTTPException(
            status_code=500, detail="Job posting not found for this resume"
        )

    try:
        language = LanguageCode(tailored_resume.language)
        cover_letters = []

        # Generate both versions
        for version in [1, 2]:
            cover_letter_text = generate_cover_letter_llm(
                tailored_resume_text=tailored_resume.content,
                job_description=job_posting.text,
                language=language,
                custom_instructions=cover_letter_request.custom_instructions,
                version=version,
            )

            cover_letter = TailoredCoverLetter(
                text=cover_letter_text,
                tailored_resume_id=tailored_resume.id,
                version=version,
            )
            db.add(cover_letter)
            db.flush()  # Flush to get the ID
            db.refresh(cover_letter)

            cover_letters.append(
                CoverLetterResponse(
                    id=cover_letter.id,
                    created_at=cover_letter.created_at,
                    text=cover_letter.text,
                    tailored_resume_id=tailored_resume.id,
                    version=cover_letter.version,
                )
            )

        db.commit()

        return CoverLetterListResponse(cover_letters=cover_letters)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error generating cover letter: {exc}"
        ) from exc


@router.get(
    "/tailor/{resume_id}/cover-letter",
    response_model=CoverLetterListResponse,
)
def get_cover_letters(
    resume_id: int,
    db: Session = Depends(get_db),
) -> CoverLetterListResponse:
    """
    Retrieve all cover letter versions for a tailored resume.

    Returns both versions (1 and 2) if they exist, otherwise 404.
    """
    tailored_resume = db.get(TailoredResume, resume_id)
    if tailored_resume is None:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    # Get all cover letters for this resume, ordered by version
    cover_letters_db = (
        db.query(TailoredCoverLetter)
        .filter(TailoredCoverLetter.tailored_resume_id == resume_id)
        .order_by(TailoredCoverLetter.version)
        .all()
    )

    if not cover_letters_db:
        raise HTTPException(
            status_code=404, detail="No cover letters found for this resume"
        )

    cover_letters = [
        CoverLetterResponse(
            id=cl.id,
            created_at=cl.created_at,
            text=cl.text,
            tailored_resume_id=cl.tailored_resume_id,
            version=cl.version,
        )
        for cl in cover_letters_db
    ]

    return CoverLetterListResponse(cover_letters=cover_letters)


@router.get("/cover-letter/{cover_letter_id}/pdf")
def get_cover_letter_pdf(
    cover_letter_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Generate and download a PDF version of a cover letter.

    Returns a PDF file that can be downloaded or viewed in a browser.
    The PDF is generated from the cover letter content with professional
    formatting suitable for business correspondence.

    Args:
        cover_letter_id: ID of the cover letter to generate PDF for.

    Returns:
        PDF response with proper headers for download.
    """
    cover_letter = db.get(TailoredCoverLetter, cover_letter_id)
    if cover_letter is None:
        raise HTTPException(
            status_code=404, detail="Cover letter not found"
        )

    try:
        pdf_bytes = generate_cover_letter_pdf(cover_letter.text)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="cover_letter_{cover_letter_id}_'
                    f'v{cover_letter.version}.pdf"'
                )
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating cover letter PDF: {exc}",
        ) from exc


