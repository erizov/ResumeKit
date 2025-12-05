"""
Recommendation endpoint for tailoring resumes to job descriptions.

The endpoint accepts either raw resume text or an uploaded file
together with a job description, plus optional tailoring options
such as languages and target roles.
"""

import sys
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

# Ensure print statements flush immediately
def _flush_print(*args, **kwargs):
    """Print and immediately flush stdout."""
    print(*args, **kwargs)
    sys.stdout.flush()
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import RATE_LIMIT_ENABLED
from ..db import get_db
from ..models import BaseResume, JobPosting, TailoredResume, User
from ..routes.auth import get_current_user
from ..schemas import LanguageCode, RecommendOptions, RecommendResult, TargetRole
from ..services.job_parser import fetch_job_description_from_url
from ..services.preset_service import get_preset_by_language_and_industry
from ..services.resume_parser import extract_text_from_upload
from ..services.tailor import generate_tailored_resumes

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


def _apply_rate_limit(func):
    """
    Conditionally apply rate limiting based on configuration.
    """
    if RATE_LIMIT_ENABLED:
        return limiter.limit("10/hour")(func)
    return func


def _parse_comma_separated_enum(
    raw: str | None,
    enum_type: type[LanguageCode] | type[TargetRole],
    default: List[LanguageCode] | List[TargetRole],
):
    """
    Parse a comma-separated list of enum values from a form field.
    """
    if not raw:
        return default

    items = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not items:
        return default

    result = []
    for item in items:
        try:
            result.append(enum_type(item))
        except ValueError as exc:
            msg = f"Invalid value '{item}' for {enum_type.__name__}"
            raise HTTPException(status_code=400, detail=msg) from exc
    return result


@router.post("/recommend", response_model=RecommendResult)
@_apply_rate_limit
async def recommend(
    request: Request,
    job_description: str = Form(""),
    job_url: str = Form(""),
    resume_text: str | None = Form(None),
    resume_file: UploadFile | None = File(None),
    languages: str | None = Form(None),
    targets: str | None = Form(None),
    aggressiveness: int = Form(2, ge=1, le=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendResult:
    """
    Produce tailored resume drafts for the provided inputs.

    The client may provide either raw resume text or an uploaded file.
    Either job_description or job_url must be provided. If job_url is
    provided, the description will be fetched from the URL.
    Tailoring options such as languages and target roles can be passed
    as comma-separated lists, for example: "en,ru" or "backend,gpt_engineer".

    Rate limited to 10 requests per hour per IP address.
    """
    _flush_print("=" * 80)
    _flush_print("[Recommend] ===== RECOMMEND ENDPOINT CALLED =====")
    _flush_print(f"[Recommend] DEBUG: User ID: {current_user.id}")
    _flush_print(f"[Recommend] DEBUG: Has job_description: {job_description is not None}")
    _flush_print(f"[Recommend] DEBUG: Has job_url: {job_url is not None}")
    _flush_print(f"[Recommend] DEBUG: Has resume_text: {resume_text is not None}")
    _flush_print(f"[Recommend] DEBUG: Has resume_file: {resume_file is not None}")
    _flush_print("=" * 80)
    
    # Normalize empty strings to None (handle both None and empty string cases)
    if job_description:
        job_description = job_description.strip()
        if not job_description:
            job_description = None
    if job_url:
        job_url = job_url.strip()
        if not job_url:
            job_url = None
    
    # Validate job description or URL
    if not job_description and not job_url:
        msg = "Either job_description or job_url must be provided."
        raise HTTPException(status_code=400, detail=msg)
    
    # Fetch job description from URL if provided
    if job_url and not job_description:
        try:
            _flush_print(f"[Recommend] DEBUG: Fetching job description from URL: {job_url}")
            job_description = await fetch_job_description_from_url(job_url)
            _flush_print(f"[Recommend] DEBUG: Fetched job description length: {len(job_description)}")
        except Exception as exc:
            msg = f"Failed to fetch job description from URL: {str(exc)}"
            _flush_print(f"[Recommend] ERROR: {msg}")
            raise HTTPException(status_code=400, detail=msg) from exc
    
    # Final check - job_description must be set at this point
    if not job_description:
        msg = "Job description is required (either provided directly or fetched from URL)."
        raise HTTPException(status_code=400, detail=msg)
    
    if not resume_text and not resume_file:
        msg = "Either resume_text or resume_file must be provided."
        raise HTTPException(status_code=400, detail=msg)

    if resume_file and not resume_text:
        base_resume = await extract_text_from_upload(resume_file)
    else:
        assert resume_text is not None
        base_resume = resume_text

    languages_list = _parse_comma_separated_enum(
        languages, LanguageCode, [LanguageCode.EN, LanguageCode.RU]
    )
    targets_list = _parse_comma_separated_enum(
        targets, TargetRole, [TargetRole.BACKEND]
    )

    options = RecommendOptions(
        languages=languages_list,
        targets=targets_list,
        aggressiveness=aggressiveness,
    )

    # Get style preset guidance based on language and industry
    # Determine industry from target role (default to tech, can be expanded)
    industry_map = {
        "backend": "tech",
        "fullstack": "tech",
        "gpt_engineer": "tech",
    }
    industry = industry_map.get(
        options.targets[0].value if options.targets else "backend", "tech"
    )

    preset_guidance = None
    for language in options.languages:
        preset = get_preset_by_language_and_industry(db, language.value, industry)
        if preset:
            # Combine preset guidance
            guidance_parts = []
            if preset.section_order:
                guidance_parts.append(f"Section Order: {preset.section_order}")
            if preset.formatting_rules:
                guidance_parts.append(f"Formatting: {preset.formatting_rules}")
            if preset.style_guidelines:
                guidance_parts.append(f"Style: {preset.style_guidelines}")
            if preset.tone_guidance:
                guidance_parts.append(f"Tone: {preset.tone_guidance}")
            if preset.length_guidelines:
                guidance_parts.append(f"Length: {preset.length_guidelines}")
            if preset.ats_keywords:
                guidance_parts.append(
                    f"ATS Keywords to consider: {preset.ats_keywords}"
                )
            if guidance_parts:
                preset_guidance = "\n".join(guidance_parts)
            break  # Use first matching preset

    # Check user's resume limit
    resume_count = db.scalar(
        select(func.count(TailoredResume.id))
        .join(BaseResume)
        .where(BaseResume.user_id == current_user.id)
    ) or 0
    
    if resume_count >= current_user.user_level:
        raise HTTPException(
            status_code=403,
            detail=f"You have reached your resume limit of {current_user.user_level}. Please delete some resumes or upgrade your account.",
        )

    _flush_print(f"[Recommend] DEBUG: About to call generate_tailored_resumes()")
    _flush_print(f"[Recommend] DEBUG: base_resume length={len(base_resume)}")
    _flush_print(f"[Recommend] DEBUG: job_description length={len(job_description)}")
    _flush_print(f"[Recommend] DEBUG: options.languages={[l.value for l in options.languages]}")
    _flush_print(f"[Recommend] DEBUG: options.targets={[t.value for t in options.targets]}")
    
    resumes = generate_tailored_resumes(
        base_resume_text=base_resume,
        job_description=job_description,
        options=options,
        preset_guidance=preset_guidance,
    )
    
    _flush_print(f"[Recommend] DEBUG: generate_tailored_resumes returned {len(resumes)} resumes")
    for i, resume in enumerate(resumes):
        _flush_print(f"[Recommend] DEBUG: Resume {i}: language={resume.language}, target={resume.target}, content_length={len(resume.content)}, notes={resume.notes}")

    # Persist base resume, job posting, and tailored variants.
    base_obj = BaseResume(text=base_resume, user_id=current_user.id)
    job_obj = JobPosting(text=job_description, user_id=current_user.id)
    db.add(base_obj)
    db.add(job_obj)
    db.flush()

    db_objs: list[TailoredResume] = []
    for r in resumes:
        db_obj = TailoredResume(
            language=r.language.value,
            target=r.target.value,
            content=r.content,
            notes=r.notes,
            base_resume_id=base_obj.id,
            job_posting_id=job_obj.id,
        )
        db.add(db_obj)
        db_objs.append(db_obj)

    db.commit()

    # Populate identifiers and timestamps on returned models so the
    # client can reference specific tailored resumes later.
    for r, db_obj in zip(resumes, db_objs, strict=False):
        r.id = db_obj.id
        r.created_at = db_obj.created_at

    return RecommendResult(resumes=resumes)


