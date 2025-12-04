"""
History and detail endpoints for tailored resumes.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import BaseResume, JobPosting, TailoredResume
from ..schemas import (
    HistoryResponse,
    KeywordCoverage,
    LanguageCode,
    TailoredResumeDetail,
    TailoredResumeSummary,
    TargetRole,
)
from ..services.docx_generator import generate_docx_from_text
from ..services.keyword_coverage import compute_coverage
from ..services.pdf_generator import generate_pdf_from_text


router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
def get_history(
    *,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    language: LanguageCode | None = Query(None),
    target: TargetRole | None = Query(None),
) -> HistoryResponse:
    """
    Return a paginated list of tailored resumes.
    """
    query = select(TailoredResume).order_by(TailoredResume.created_at.desc())

    if language is not None:
        query = query.where(TailoredResume.language == language.value)
    if target is not None:
        query = query.where(TailoredResume.target == target.value)

    total_query = select(func.count()).select_from(query.subquery())
    total = db.execute(total_query).scalar_one()

    rows = db.execute(query.limit(limit).offset(offset)).scalars().all()

    items: list[TailoredResumeSummary] = []
    for row in rows:
        items.append(
            TailoredResumeSummary(
                id=row.id,
                created_at=row.created_at,
                language=LanguageCode(row.language),
                target=TargetRole(row.target),
            )
        )

    return HistoryResponse(items=items, total=total)


@router.get("/tailor/{resume_id}", response_model=TailoredResumeDetail)
def get_tailored_resume(
    resume_id: int,
    db: Session = Depends(get_db),
) -> TailoredResumeDetail:
    """
    Retrieve a single tailored resume, including source texts.
    """
    row = db.get(TailoredResume, resume_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    base_resume = db.get(BaseResume, row.base_resume_id)
    job_posting = db.get(JobPosting, row.job_posting_id)
    if base_resume is None or job_posting is None:
        raise HTTPException(
            status_code=500,
            detail="Linked base resume or job posting is missing",
        )

    return TailoredResumeDetail(
        id=row.id,
        created_at=row.created_at,
        language=LanguageCode(row.language),
        target=TargetRole(row.target),
        content=row.content,
        notes=row.notes,
        base_resume_text=base_resume.text,
        job_description=job_posting.text,
    )


@router.get("/tailor/{resume_id}/coverage", response_model=KeywordCoverage)
def get_keyword_coverage(
    resume_id: int,
    db: Session = Depends(get_db),
) -> KeywordCoverage:
    """
    Analyze keyword coverage between the base resume and job description.

    Extracts technology and skill keywords from both texts and computes:
    - Matched keywords (present in both)
    - Missing keywords (in JD but not in resume)
    - Coverage score (0.0 to 1.0)

    This helps identify which skills from the job description are
    already present in the resume and which might need to be added.
    """
    row = db.get(TailoredResume, resume_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    base_resume = db.get(BaseResume, row.base_resume_id)
    job_posting = db.get(JobPosting, row.job_posting_id)
    if base_resume is None or job_posting is None:
        raise HTTPException(
            status_code=500,
            detail="Linked base resume or job posting is missing",
        )

    coverage_data = compute_coverage(base_resume.text, job_posting.text)

    return KeywordCoverage(**coverage_data)


@router.get("/tailor/{resume_id}/pdf")
def get_tailored_resume_pdf(
    resume_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Generate and download a PDF version of the tailored resume.

    Returns a PDF file that can be downloaded or viewed in a browser.
    The PDF is generated from the tailored resume content with basic
    formatting suitable for printing or sharing.
    """
    row = db.get(TailoredResume, resume_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    try:
        pdf_bytes = generate_pdf_from_text(row.content)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="resume_{resume_id}_{row.language}_'
                    f'{row.target}.pdf"'
                )
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {exc}",
        ) from exc


@router.get("/tailor/{resume_id}/docx")
def get_tailored_resume_docx(
    resume_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Generate and download a DOCX version of the tailored resume.

    Returns a DOCX file that can be downloaded or opened in Word.
    The DOCX is generated from the tailored resume content with basic
    formatting suitable for editing or sharing.
    """
    row = db.get(TailoredResume, resume_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tailored resume not found")

    try:
        docx_bytes = generate_docx_from_text(row.content)

        return Response(
            content=docx_bytes,
            media_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            headers={
                "Content-Disposition": (
                    f'attachment; filename="resume_{resume_id}_{row.language}_'
                    f'{row.target}.docx"'
                )
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating DOCX: {exc}",
        ) from exc


