"""
Metrics and analytics endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import BaseResume, JobPosting, TailoredResume, TailoredCoverLetter


router = APIRouter()


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)) -> dict:
    """
    Return basic application metrics.

    Provides aggregate statistics about resumes, job postings,
    tailored resumes, and cover letters.
    """
    total_base_resumes = db.scalar(select(func.count(BaseResume.id)))
    total_job_postings = db.scalar(select(func.count(JobPosting.id)))
    total_tailored_resumes = db.scalar(select(func.count(TailoredResume.id)))
    total_cover_letters = db.scalar(select(func.count(TailoredCoverLetter.id)))

    return {
        "total_base_resumes": total_base_resumes or 0,
        "total_job_postings": total_job_postings or 0,
        "total_tailored_resumes": total_tailored_resumes or 0,
        "total_cover_letters": total_cover_letters or 0,
    }


