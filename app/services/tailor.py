"""
Tailoring logic for generating resume variants.

By default this module uses deterministic stub content so unit tests can
run without external dependencies. When the RESUMEKIT_USE_OPENAI
environment variable is set to a truthy value and OPENAI_API_KEY is
configured, it will delegate to the OpenAI-backed implementation.
"""

import os
from typing import List

from ..schemas import LanguageCode, RecommendOptions, TailoredResume, TargetRole
from .llm_client import generate_tailored_resume_llm


def generate_tailored_resumes(
    *,
    base_resume_text: str,
    job_description: str,
    options: RecommendOptions,
    preset_guidance: str | None = None,
) -> List[TailoredResume]:
    """
    Generate tailored resume drafts for the given languages and targets.

    The implementation uses a deterministic stub unless OpenAI
    integration is explicitly enabled via environment variables.
    """
    use_llm = os.getenv("RESUMEKIT_USE_OPENAI", "").lower() in {
        "1",
        "true",
        "yes",
    }

    resumes: list[TailoredResume] = []
    for language in options.languages:
        for target in options.targets:
            if use_llm:
                content = generate_tailored_resume_llm(
                    base_resume_text=base_resume_text,
                    job_description=job_description,
                    language=language,
                    target=target,
                    aggressiveness=options.aggressiveness,
                    preset_guidance=preset_guidance,
                )
                notes = "Generated using OpenAI."
            else:
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


