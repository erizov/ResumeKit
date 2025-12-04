"""
Cover letter generation endpoints.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..config import RATE_LIMIT_ENABLED
from ..db import get_db
from ..models import TailoredResume, TailoredCoverLetter
from ..schemas import CoverLetterRequest, CoverLetterResponse, LanguageCode
from ..services.llm_client import generate_cover_letter_llm

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


def _apply_rate_limit(func):
    """
    Conditionally apply rate limiting based on configuration.
    """
    if RATE_LIMIT_ENABLED:
        return limiter.limit("5/hour")(func)
    return func


@router.post("/tailor/{resume_id}/cover-letter", response_model=CoverLetterResponse)
@_apply_rate_limit
def generate_cover_letter(
    request: Request,
    resume_id: int,
    cover_letter_request: CoverLetterRequest,
    db: Session = Depends(get_db),
) -> CoverLetterResponse:
    """
    Generate a cover letter for a specific tailored resume.

    Uses OpenAI to generate a professional cover letter based on the
    tailored resume content and the original job description.
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
        cover_letter_text = generate_cover_letter_llm(
            tailored_resume_text=tailored_resume.content,
            job_description=job_posting.text,
            language=language,
            custom_instructions=cover_letter_request.custom_instructions,
        )

        cover_letter = TailoredCoverLetter(
            text=cover_letter_text,
            tailored_resume_id=tailored_resume.id,
        )
        db.add(cover_letter)
        db.commit()
        db.refresh(cover_letter)

        return CoverLetterResponse(
            id=cover_letter.id,
            created_at=cover_letter.created_at,
            text=cover_letter.text,
            tailored_resume_id=tailored_resume.id,
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error generating cover letter: {exc}"
        ) from exc


@router.get("/tailor/{resume_id}/cover-letter", response_model=CoverLetterResponse)
def get_cover_letter(
    resume_id: int,
    db: Session = Depends(get_db),
) -> CoverLetterResponse:
    """
    Retrieve the most recent cover letter for a tailored resume.

    Returns the latest cover letter if one exists, otherwise 404.
    """
    tailored_resume = db.get(TailoredResume, resume_id)
    if tailored_resume is None:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    # Get the most recent cover letter
    cover_letter = (
        db.query(TailoredCoverLetter)
        .filter(TailoredCoverLetter.tailored_resume_id == resume_id)
        .order_by(TailoredCoverLetter.created_at.desc())
        .first()
    )

    if cover_letter is None:
        raise HTTPException(
            status_code=404, detail="No cover letter found for this resume"
        )

    return CoverLetterResponse(
        id=cover_letter.id,
        created_at=cover_letter.created_at,
        text=cover_letter.text,
        tailored_resume_id=tailored_resume.id,
    )


