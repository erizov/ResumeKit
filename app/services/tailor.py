"""
Tailoring logic for generating resume variants.

By default this module uses deterministic stub content so unit tests can
run without external dependencies. When the RESUMEKIT_USE_OPENAI
environment variable is set to a truthy value and OPENAI_API_KEY is
configured, it will delegate to the OpenAI-backed implementation.
"""

import os
import sys
from typing import List

from ..config import OPENAI_API_KEY, RESUMEKIT_USE_OPENAI
from ..schemas import LanguageCode, RecommendOptions, TailoredResume, TargetRole
from .llm_client import generate_tailored_resume_llm

# Ensure print statements flush immediately
def _flush_print(*args, **kwargs):
    """Print and immediately flush stdout."""
    print(*args, **kwargs)
    sys.stdout.flush()


def generate_tailored_resumes(
    *,
    base_resume_text: str,
    job_description: str,
    options: RecommendOptions,
    preset_guidance: str | None = None,
) -> List[TailoredResume]:
    """
    Generate tailored resume drafts for the given languages and targets.

    The implementation uses OpenAI if available, otherwise falls back to
    a deterministic stub. OpenAI is used if:
    - RESUMEKIT_USE_OPENAI is explicitly set to a truthy value, OR
    - OPENAI_API_KEY is configured (auto-enable)
    """
    # Auto-enable OpenAI if API key is configured, unless explicitly disabled
    # Prefer value from config (loaded via .env), fallback to direct env read
    explicit_flag = (RESUMEKIT_USE_OPENAI or os.getenv("RESUMEKIT_USE_OPENAI", "")).lower()
    has_api_key = bool(OPENAI_API_KEY)
    
    use_llm = (
        explicit_flag in {"1", "true", "yes"} or
        (has_api_key and explicit_flag not in {"0", "false", "no"})
    )
    
    _flush_print(f"[Tailor] DEBUG: explicit_flag='{explicit_flag}', has_api_key={has_api_key}, use_llm={use_llm}")
    _flush_print(f"[Tailor] DEBUG: OPENAI_API_KEY present: {bool(OPENAI_API_KEY)}")
    if OPENAI_API_KEY:
        _flush_print(f"[Tailor] DEBUG: OPENAI_API_KEY length: {len(OPENAI_API_KEY)}, first 10 chars: {OPENAI_API_KEY[:10]}...")
    else:
        _flush_print(f"[Tailor] WARNING: OPENAI_API_KEY is not set! LLM will not be used.")
        _flush_print(f"[Tailor] WARNING: Set OPENAI_API_KEY environment variable to enable OpenAI calls.")

    if not use_llm:
        _flush_print(f"[Tailor] WARNING: LLM is disabled. Using stub content instead of OpenAI.")
        _flush_print(f"[Tailor] WARNING: To enable OpenAI, set OPENAI_API_KEY or RESUMEKIT_USE_OPENAI=1")

    resumes: list[TailoredResume] = []
    for language in options.languages:
        for target in options.targets:
            _flush_print(f"[Tailor] DEBUG: Processing language={language.value}, target={target.value}")
            
            if use_llm:
                _flush_print(f"[Tailor] DEBUG: Calling generate_tailored_resume_llm() for language={language.value}...")
                content = generate_tailored_resume_llm(
                    base_resume_text=base_resume_text,
                    job_description=job_description,
                    language=language,
                    target=target,
                    aggressiveness=options.aggressiveness,
                    preset_guidance=preset_guidance,
                )
                _flush_print(f"[Tailor] DEBUG: Received content from LLM for {language.value}, length={len(content)}")
                notes = f"Generated using OpenAI for {language.value}."
            else:
                _flush_print(f"[Tailor] DEBUG: Using stub content (LLM disabled)")
                content = _build_stub_content(
                    language=language,
                    target=target,
                    base_resume_text=base_resume_text,
                    job_description=job_description,
                    aggressiveness=options.aggressiveness,
                )
                notes = (
                    "Stub tailoring only. LLM-backed rewriting is disabled "
                    "or not configured."
                )

            resumes.append(
                TailoredResume(
                    language=language,
                    target=target,
                    content=content,
                    notes=notes,
                )
            )
    return resumes


def _build_stub_content(
    *,
    language: LanguageCode,
    target: TargetRole,
    base_resume_text: str,
    job_description: str,
    aggressiveness: int,
) -> str:
    """
    Build deterministic placeholder content for a single variant.
    """
    header = (
        f"[TAILORED RESUME - lang={language.value}, "
        f"target={target.value}, aggressiveness={aggressiveness}]"
    )
    jd_snippet = job_description.strip().splitlines()[0:3]
    jd_preview = " ".join(line.strip() for line in jd_snippet if line.strip())
    body_parts = [
        header,
        "",
        "=== JOB DESCRIPTION PREVIEW ===",
        jd_preview or "(no job description provided)",
        "",
        "=== BASE RESUME START ===",
        base_resume_text.strip(),
        "=== BASE RESUME END ===",
    ]
    return "\n".join(body_parts)


