"""
OpenAI client wrapper for resume tailoring.

This module centralizes all interaction with the OpenAI API so that
the rest of the application can depend on a small, well-typed surface.
"""

from __future__ import annotations

import json
from typing import Optional

from openai import OpenAI

from ..config import OPENAI_API_BASE, OPENAI_API_KEY
from ..schemas import LanguageCode, StructuredResume, TargetRole


_CLIENT: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """
    Lazily construct an OpenAI client.
    """
    global _CLIENT
    if _CLIENT is None:
        api_key = OPENAI_API_KEY
        if not api_key:
            msg = "OPENAI_API_KEY environment variable is not set."
            raise RuntimeError(msg)
        if OPENAI_API_BASE:
            _CLIENT = OpenAI(api_key=api_key, base_url=OPENAI_API_BASE)
        else:
            _CLIENT = OpenAI(api_key=api_key)
    return _CLIENT


def generate_tailored_resume_llm(
    *,
    base_resume_text: str,
    job_description: str,
    language: LanguageCode,
    target: TargetRole,
    aggressiveness: int,
    preset_guidance: str | None = None,
) -> str:
    """
    Call the OpenAI API to generate a single tailored resume variant.

    The current implementation returns plain text content which can be
    rendered directly or further processed.
    """
    from ..config import RAG_ENABLED, RAG_TOP_K
    from .rag_service import get_rag_service

    client = _get_client()

    style_hint = _language_style_hint(language)
    target_label = target.value.replace("_", " ")

    # Retrieve best practices using RAG if enabled
    rag_context = ""
    if RAG_ENABLED:
        try:
            rag_service = get_rag_service()
            best_practices = rag_service.retrieve_best_practices(
                language=language,
                target_role=target,
                job_description=job_description,
                top_k=RAG_TOP_K,
            )

            if best_practices:
                rag_context = "\n\nMARKET-SPECIFIC BEST PRACTICES:\n"
                rag_context += "=" * 50 + "\n"
                for i, practice in enumerate(best_practices, 1):
                    # Truncate each practice to avoid token limits
                    practice_text = practice[:1000] + "..." if len(practice) > 1000 else practice
                    rag_context += f"\n[Best Practice {i}]\n{practice_text}\n"
                rag_context += "=" * 50 + "\n"
        except Exception as e:
            # If RAG fails, continue without it
            print(f"Warning: RAG retrieval failed: {e}")

    # Add preset guidance if provided
    preset_context = ""
    if preset_guidance:
        preset_context = f"\n\nSTYLE PRESET GUIDANCE:\n{preset_guidance}\n"

    system_prompt = (
        "You are an assistant that rewrites CVs truthfully and concisely. "
        "You must never invent jobs, employers, dates, or achievements. "
        "You may only rephrase and re-order the existing material. "
        "Use a structure suitable for modern ATS systems."
        f"{rag_context}"
        f"{preset_context}"
    )

    user_prompt = (
        f"LANGUAGE: {language.value}\n"
        f"TARGET ROLE: {target_label}\n"
        f"AGGRESSIVENESS: {aggressiveness} "
        "(1=minimal edits, 2=balanced, 3=strong rewrite of wording only)\n"
        f"STYLE HINTS: {style_hint}\n\n"
        "JOB DESCRIPTION:\n"
        f"{job_description}\n\n"
        "BASE RESUME:\n"
        f"{base_resume_text}\n\n"
        "TASK:\n"
        "Rewrite the resume for this specific job. "
        "Keep all employers, titles, and dates factual. "
        "Prioritise bullets and sections most relevant to the job. "
        "Return ONLY the final resume text, no explanations.\n\n"
        "FORMATTING REQUIREMENTS:\n"
        "- Remove all '--' separators and divider lines\n"
        "- Remove excessive empty lines (maximum 1 empty line between sections)\n"
        "- Keep the entire resume under 2 pages\n"
        "- Format job titles and dates on the same line with dates aligned to the right\n"
        "  Example: '*AVP / Программист-аналитик*  1998 – 2002'\n"
        "- Use consistent spacing and formatting throughout\n"
        "- Be concise and remove redundant information if needed to stay under 2 pages"
    )

    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )

    content = completion.choices[0].message.content or ""
    return content.strip()


def generate_cover_letter_llm(
    *,
    tailored_resume_text: str,
    job_description: str,
    language: LanguageCode,
    custom_instructions: str | None = None,
) -> str:
    """
    Generate a cover letter based on a tailored resume and job description.

    Args:
        tailored_resume_text: The tailored resume content.
        job_description: The job description text.
        language: Target language for the cover letter.
        custom_instructions: Optional custom instructions for the cover letter.

    Returns:
        Generated cover letter text.
    """
    client = _get_client()

    style_hint = _language_style_hint(language)

    system_prompt = (
        "You are an assistant that writes professional cover letters. "
        "Write a compelling cover letter that highlights the candidate's "
        "relevant experience and skills from the resume. "
        "Keep it concise, professional, and tailored to the specific job. "
        "Do not invent information not present in the resume."
    )

    user_prompt = (
        f"LANGUAGE: {language.value}\n"
        f"STYLE HINTS: {style_hint}\n\n"
    )

    if custom_instructions:
        user_prompt += f"CUSTOM INSTRUCTIONS: {custom_instructions}\n\n"

    user_prompt += (
        "JOB DESCRIPTION:\n"
        f"{job_description}\n\n"
        "TAILORED RESUME:\n"
        f"{tailored_resume_text}\n\n"
        "TASK:\n"
        "Write a professional cover letter for this position. "
        "Highlight relevant experience and skills from the resume. "
        "Keep it concise (3-4 paragraphs). "
        "Return ONLY the cover letter text, no explanations."
    )

    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
    )

    content = completion.choices[0].message.content or ""
    return content.strip()


def parse_resume_to_structured(resume_text: str) -> StructuredResume:
    """
    Parse a resume text into structured JSON format using OpenAI.

    Extracts name, contact info, experience, education, skills, etc.
    into a structured format that can be used for keyword matching
    and better tailoring.

    Raises:
        RuntimeError: If OpenAI API key is not configured.
    """
    try:
        client = _get_client()
    except RuntimeError:
        # If OpenAI is not configured, return minimal structured resume
        return StructuredResume(summary=resume_text[:500] if resume_text else None)

    system_prompt = (
        "You are an assistant that extracts structured data from resumes. "
        "Parse the resume text and return ONLY valid JSON matching this schema:\n"
        "{\n"
        '  "name": "string or null",\n'
        '  "email": "string or null",\n'
        '  "phone": "string or null",\n'
        '  "location": "string or null",\n'
        '  "linkedin": "string or null",\n'
        '  "github": "string or null",\n'
        '  "summary": "string or null",\n'
        '  "experience": [\n'
        "    {\n"
        '      "title": "string",\n'
        '      "company": "string",\n'
        '      "start_date": "string or null",\n'
        '      "end_date": "string or null",\n'
        '      "description": ["string"],\n'
        '      "technologies": ["string"]\n'
        "    }\n"
        "  ],\n"
        '  "education": [\n'
        "    {\n"
        '      "degree": "string",\n'
        '      "institution": "string",\n'
        '      "field_of_study": "string or null",\n'
        '      "graduation_date": "string or null"\n'
        "    }\n"
        "  ],\n"
        '  "skills": ["string"],\n'
        '  "projects": [{"name": "string", "description": "string"}]\n'
        "}\n"
        "Return ONLY the JSON object, no markdown, no explanations."
    )

    user_prompt = f"Parse this resume:\n\n{resume_text}"

    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,  # Low temperature for consistent parsing
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
        return StructuredResume(**data)
    except (json.JSONDecodeError, ValueError) as exc:
        # Fallback: return minimal structured resume
        return StructuredResume(
            summary=resume_text[:500] if resume_text else None
        )


def _language_style_hint(language: LanguageCode) -> str:
    """
    Provide high-level guidance for each supported language.
    """
    if language is LanguageCode.RU:
        return (
            "Write in Russian, using concise, professional business style. "
            "Use Russian section headings and terminology that are typical "
            "for Russian-speaking IT job markets."
        )

    return (
        "Write in English, concise and results-oriented. "
        "Use strong action verbs and quantify impact where possible."
    )


