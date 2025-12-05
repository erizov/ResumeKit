"""
OpenAI client wrapper for resume tailoring.

This module centralizes all interaction with the OpenAI API so that
the rest of the application can depend on a small, well-typed surface.
"""

from __future__ import annotations

import json
import sys
from typing import Optional

from openai import OpenAI

from ..config import OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL
from ..schemas import LanguageCode, StructuredResume, TargetRole
from .humanizer import humanize_text

# Ensure print statements flush immediately
def _flush_print(*args, **kwargs):
    """Print and immediately flush stdout."""
    print(*args, **kwargs)
    sys.stdout.flush()


_CLIENT: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """
    Lazily construct an OpenAI client.
    """
    global _CLIENT
    if _CLIENT is None:
        _flush_print(f"[LLM Client] DEBUG: Initializing OpenAI client...")
        _flush_print(f"[LLM Client] DEBUG: OPENAI_API_KEY present: {bool(OPENAI_API_KEY)}")
        _flush_print(f"[LLM Client] DEBUG: OPENAI_API_BASE: {OPENAI_API_BASE}")
        if not OPENAI_API_KEY:
            msg = "OPENAI_API_KEY environment variable is not set."
            _flush_print(f"[LLM Client] ERROR: {msg}")
            raise RuntimeError(msg)
        _CLIENT = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        _flush_print(f"[LLM Client] DEBUG: OpenAI client initialized successfully")
    else:
        _flush_print(f"[LLM Client] DEBUG: Using existing OpenAI client")
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

    _flush_print(f"[LLM Client] DEBUG: Starting generate_tailored_resume_llm()")
    _flush_print(f"[LLM Client] DEBUG: RAG_ENABLED={RAG_ENABLED}, RAG_TOP_K={RAG_TOP_K}")
    _flush_print(f"[LLM Client] DEBUG: Language={language.value}, Target={target.value}")
    
    _flush_print(f"[LLM Client] DEBUG: Getting OpenAI client...")
    client = _get_client()
    _flush_print(f"[LLM Client] DEBUG: OpenAI client obtained")

    style_hint = _language_style_hint(language)
    target_label = target.value.replace("_", " ")

    # Retrieve best practices using RAG if enabled
    rag_context = ""
    if RAG_ENABLED:
        _flush_print(f"[LLM Client] DEBUG: RAG enabled, retrieving best practices...")
        try:
            rag_service = get_rag_service()
            best_practices = rag_service.retrieve_best_practices(
                language=language,
                target_role=target,
                job_description=job_description,
                top_k=RAG_TOP_K,
            )

            if best_practices:
                _flush_print(f"[LLM Client] DEBUG: RAG returned {len(best_practices)} best practices")
                rag_context = "\n\nMARKET-SPECIFIC BEST PRACTICES:\n"
                rag_context += "=" * 50 + "\n"
                for i, practice in enumerate(best_practices, 1):
                    # Truncate each practice to avoid token limits
                    practice_text = practice[:1000] + "..." if len(practice) > 1000 else practice
                    rag_context += f"\n[Best Practice {i}]\n{practice_text}\n"
                rag_context += "=" * 50 + "\n"
            else:
                _flush_print(f"[LLM Client] DEBUG: RAG returned no best practices")
        except Exception as e:
            # If RAG fails, continue without it
            _flush_print(f"[LLM Client] WARNING: RAG retrieval failed: {e}")
            import traceback
            traceback.print_exc()

    # Add preset guidance if provided
    preset_context = ""
    if preset_guidance:
        preset_context = f"\n\nSTYLE PRESET GUIDANCE:\n{preset_guidance}\n"

    system_prompt = (
        "You are an expert resume tailoring assistant. Your job is to "
        "rewrite and customize resumes to match specific job descriptions. "
        "CRITICAL REQUIREMENTS:\n"
        "1. You must NEVER invent jobs, employers, dates, or achievements.\n"
        "2. You may ONLY rephrase, reorder, and emphasize existing material.\n"
        "3. You MUST tailor the resume to highlight skills and experience "
        "that match the job description.\n"
        "4. Prioritize and reorder sections/bullets to match job requirements.\n"
        "5. Use keywords from the job description naturally in your rewrites.\n"
        "6. Remove or de-emphasize irrelevant experience if needed to stay "
        "under 2 pages.\n"
        "7. Use a structure suitable for modern ATS systems.\n"
        "8. Write in a natural, human style. Avoid AI stigmas like: "
        "excessive use of 'leverage', 'utilize', 'robust', 'cutting-edge', "
        "'seamlessly', 'synergy'. Use simple, direct language. "
        "Vary sentence structure naturally. Don't be overly enthusiastic "
        "or perfect.\n"
        f"{rag_context}"
        f"{preset_context}"
    )

    # Explicitly state the output language requirement
    language_instruction = ""
    if language is LanguageCode.RU:
        language_instruction = (
            "CRITICAL: You MUST write the ENTIRE resume in RUSSIAN. "
            "All text, section headings, and content must be in Russian. "
            "Use Russian business terminology and formatting conventions.\n\n"
        )
    else:
        language_instruction = (
            "CRITICAL: You MUST write the ENTIRE resume in ENGLISH. "
            "All text, section headings, and content must be in English. "
            "Use English business terminology and formatting conventions.\n\n"
        )
    
    user_prompt = (
        f"LANGUAGE: {language.value.upper()}\n"
        f"TARGET ROLE: {target_label}\n"
        f"AGGRESSIVENESS: {aggressiveness} "
        "(1=minimal edits, 2=balanced, 3=strong rewrite of wording only)\n"
        f"STYLE HINTS: {style_hint}\n\n"
        f"{language_instruction}"
        "JOB DESCRIPTION:\n"
        f"{job_description}\n\n"
        "BASE RESUME:\n"
        f"{base_resume_text}\n\n"
        "TASK:\n"
        "Rewrite and tailor the resume specifically for this job description. "
        "You MUST customize the content to match the job requirements:\n"
        "- Reorder sections to put most relevant experience first\n"
        "- Rewrite bullet points to emphasize skills mentioned in the job "
        "description\n"
        "- Use keywords from the job description naturally throughout\n"
        "- Remove or minimize irrelevant experience if needed\n"
        "- Keep all employers, titles, and dates 100% factual (never invent)\n"
        "- Make sure the tailored resume is clearly different from the "
        "original base resume\n"
        "- IMPORTANT: The output language MUST match the LANGUAGE specified above\n"
        "Return ONLY the final tailored resume text, no explanations or "
        "metadata.\n\n"
        "FORMATTING REQUIREMENTS:\n"
        "- Remove all '--' separators and divider lines\n"
        "- Remove excessive empty lines (maximum 1 empty line between sections)\n"
        "- Keep the entire resume under 2 pages\n"
        "- Format job titles and dates on the same line with dates aligned to the right\n"
        "  Example: '*AVP / Программист-аналитик*  1998 – 2002'\n"
        "- Use consistent spacing and formatting throughout\n"
        "- Be concise and remove redundant information if needed to stay under 2 pages"
    )

    _flush_print(f"[LLM Client] DEBUG: Calling OpenAI API with model={OPENAI_MODEL}")
    _flush_print(f"[LLM Client] DEBUG: System prompt length={len(system_prompt)}")
    _flush_print(f"[LLM Client] DEBUG: User prompt length={len(user_prompt)}")
    _flush_print(f"[LLM Client] DEBUG: Job description length={len(job_description)}")
    _flush_print(f"[LLM Client] DEBUG: Base resume length={len(base_resume_text)}")
    _flush_print(f"[LLM Client] DEBUG: Language={language.value}, Target={target.value}")
    
    try:
        _flush_print(f"[LLM Client] INFO: Making OpenAI API call...")
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        _flush_print(f"[LLM Client] DEBUG: OpenAI API call successful")
        _flush_print(f"[LLM Client] DEBUG: Response choices count={len(completion.choices)}")
    except Exception as e:
        _flush_print(f"[LLM Client] ERROR: OpenAI API call failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        error_msg = (
            f"OpenAI API error: {str(e)}. "
            "Falling back to base resume with tailoring notes."
        )
        _flush_print(f"[LLM Client] {error_msg}")
        # Return base resume with a note that tailoring failed
        return (
            f"[TAILORING FAILED - API Error]\n"
            f"Error: {str(e)}\n\n"
            f"Original resume:\n{base_resume_text}"
        )

    content = completion.choices[0].message.content or ""
    _flush_print(f"[LLM Client] DEBUG: Raw response length={len(content)}")
    cleaned_content = content.strip()
    _flush_print(f"[LLM Client] DEBUG: Cleaned content length={len(cleaned_content)}")
    
    # Validate that we got a tailored resume, not just the original
    if not cleaned_content or len(cleaned_content) < 50:
        _flush_print(
            "[LLM Client] Warning: Received very short or empty response. "
            "Falling back to base resume."
        )
        return (
            f"[TAILORING FAILED - Empty Response]\n\n"
            f"Original resume:\n{base_resume_text}"
        )
    
    # Check if the response is suspiciously similar to the base resume
    # (simple heuristic: if more than 90% of base resume words appear in same order)
    base_words = base_resume_text.lower().split()
    response_words = cleaned_content.lower().split()
    if len(base_words) > 0 and len(response_words) > 0:
        # Simple check: if response is almost identical length and structure
        length_ratio = len(response_words) / len(base_words)
        if 0.95 <= length_ratio <= 1.05 and cleaned_content.strip() == base_resume_text.strip():
            _flush_print(
                "[LLM Client] Warning: Response appears identical to base resume. "
                "This may indicate the model didn't tailor properly."
            )
    
    # Post-process to clean formatting
    from .resume_formatter import clean_resume_text, format_dates_on_right
    
    cleaned_content = clean_resume_text(cleaned_content)
    cleaned_content = format_dates_on_right(cleaned_content)
    
    # Humanize to reduce AI stigmas
    cleaned_content = humanize_text(
        cleaned_content,
        language=language.value,
        apply_variations=True
    )
    
    return cleaned_content


def generate_cover_letter_llm(
    *,
    tailored_resume_text: str,
    job_description: str,
    language: LanguageCode,
    custom_instructions: str | None = None,
    version: int = 1,
) -> str:
    """
    Generate a cover letter based on a tailored resume and job description.

    Args:
        tailored_resume_text: The tailored resume content.
        job_description: The job description text.
        language: Target language for the cover letter.
        custom_instructions: Optional custom instructions for the cover letter.
        version: Version number (1 or 2) to generate different styles.

    Returns:
        Generated cover letter text.
    """
    client = _get_client()

    style_hint = _language_style_hint(language)

    # Different styles for different versions
    if version == 1:
        style_guidance = (
            "Write a traditional, formal cover letter. "
            "Use a professional tone with clear structure: "
            "introduction, body paragraphs highlighting experience, "
            "and a closing statement. Focus on qualifications and "
            "achievements."
        )
    else:  # version == 2
        style_guidance = (
            "Write a modern, results-oriented cover letter. "
            "Use a more conversational but still professional tone. "
            "Lead with impact and specific achievements. "
            "Show enthusiasm and cultural fit. "
            "Be more concise and action-oriented."
        )

    system_prompt = (
        "You are an assistant that writes professional cover letters. "
        "Write a compelling cover letter that highlights the candidate's "
        "relevant experience and skills from the resume. "
        "Keep it concise, professional, and tailored to the specific job. "
        "Do not invent information not present in the resume. "
        "CRITICAL: Write in a natural, human style. Avoid AI stigmas: "
        "don't overuse 'leverage', 'utilize', 'robust', 'cutting-edge', "
        "'seamlessly', 'synergy', 'paradigm'. Use conversational language. "
        "Vary sentence structure. Be genuine, not overly enthusiastic. "
        "Write like a real person, not a perfect AI."
    )

    user_prompt = (
        f"LANGUAGE: {language.value}\n"
        f"STYLE HINTS: {style_hint}\n"
        f"VERSION {version} STYLE: {style_guidance}\n\n"
    )

    if custom_instructions:
        user_prompt += f"CUSTOM INSTRUCTIONS: {custom_instructions}\n\n"

    user_prompt += (
        "JOB DESCRIPTION:\n"
        f"{job_description}\n\n"
        "TAILORED RESUME:\n"
        f"{tailored_resume_text}\n\n"
        "TASK:\n"
        "Write a professional cover letter for this position following "
        f"the Version {version} style guidance above. "
        "Highlight relevant experience and skills from the resume. "
        "Keep it concise (3-4 paragraphs). "
        "Return ONLY the cover letter text, no explanations."
    )

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,  # Slightly higher for more natural variation
        )
    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        _flush_print(f"[LLM Client] {error_msg}")
        raise RuntimeError(f"Failed to generate cover letter: {error_msg}")

    content = completion.choices[0].message.content or ""
    cleaned = content.strip()
    
    # Humanize to reduce AI stigmas
    cleaned = humanize_text(
        cleaned,
        language=language.value,
        apply_variations=True
    )
    
    return cleaned


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

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for consistent parsing
            response_format={"type": "json_object"},
        )
    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        _flush_print(f"[LLM Client] {error_msg}")
        # Return minimal structured resume on error
        return StructuredResume(
            summary=resume_text[:500] if resume_text else None
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


