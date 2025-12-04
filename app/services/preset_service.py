"""
Service for managing and retrieving style presets.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import StylePreset


def get_preset_by_language_and_industry(
    db: Session, language: str, industry: str
) -> Optional[StylePreset]:
    """
    Get active preset for specific language and industry.

    Args:
        db: Database session
        language: Language code (e.g., "ru", "en")
        industry: Industry name (e.g., "tech", "finance")

    Returns:
        StylePreset if found, None otherwise
    """
    stmt = select(StylePreset).where(
        StylePreset.language == language,
        StylePreset.industry == industry,
        StylePreset.is_active == True,  # noqa: E712
    )
    result = db.execute(stmt).scalar_one_or_none()
    return result


def get_all_presets(db: Session, active_only: bool = True) -> List[StylePreset]:
    """
    Get all style presets.

    Args:
        db: Database session
        active_only: If True, only return active presets

    Returns:
        List of StylePreset objects
    """
    stmt = select(StylePreset)
    if active_only:
        stmt = stmt.where(StylePreset.is_active == True)  # noqa: E712
    stmt = stmt.order_by(StylePreset.language, StylePreset.industry, StylePreset.name)
    result = db.execute(stmt).scalars().all()
    return list(result)


def create_preset(db: Session, preset_data: dict) -> StylePreset:
    """
    Create a new style preset.

    Args:
        db: Database session
        preset_data: Dictionary with preset fields

    Returns:
        Created StylePreset object
    """
    preset = StylePreset(**preset_data)
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


def initialize_default_presets(db: Session) -> None:
    """
    Initialize default style presets in the database.

    Creates presets for common language/industry combinations.
    """
    from datetime import UTC, datetime

    default_presets = [
        # Tech Industry - Backend
        {
            "name": "Russian Tech Backend",
            "language": "ru",
            "industry": "tech",
            "description": "Russian market style for backend developers",
            "section_order": "Personal Info (with photo), Summary, Work Experience, Education, Skills, Languages",
            "formatting_rules": "2-3 pages, formal tone, professional photo required, detailed descriptions",
            "style_guidelines": "Use formal language (Вы), include all relevant technologies, detailed bullet points (5-8 per role)",
            "ats_keywords": "Python, FastAPI, PostgreSQL, Docker, Kubernetes, микросервисы, REST API",
            "tone_guidance": "Formal, professional, respectful. Avoid casual expressions.",
            "length_guidelines": "2-3 pages for experienced professionals, 1-2 pages for entry-level",
            "is_active": True,
        },
        {
            "name": "US Tech Backend",
            "language": "en",
            "industry": "tech",
            "description": "US market style for backend developers",
            "section_order": "Header, Professional Summary, Work Experience, Education, Skills",
            "formatting_rules": "1-2 pages, no photo, action verbs, metrics-focused, ATS-optimized",
            "style_guidelines": "Start bullets with action verbs, include quantifiable achievements, focus on results",
            "ats_keywords": "Python, FastAPI, REST API, PostgreSQL, Docker, Kubernetes, microservices, CI/CD",
            "tone_guidance": "Professional, results-focused, concise. Use strong action verbs.",
            "length_guidelines": "1 page for <10 years experience, 2 pages for 10+ years",
            "is_active": True,
        },
        # Tech Industry - Fullstack
        {
            "name": "Russian Tech Fullstack",
            "language": "ru",
            "industry": "tech",
            "description": "Russian market style for fullstack developers",
            "section_order": "Personal Info (with photo), Summary, Work Experience, Education, Skills, Languages",
            "formatting_rules": "2-3 pages, formal tone, professional photo, frontend and backend skills",
            "style_guidelines": "Highlight both frontend and backend experience, include full technology stack",
            "ats_keywords": "React, Vue, Angular, Python, Node.js, PostgreSQL, MongoDB, Docker",
            "tone_guidance": "Formal, professional, comprehensive",
            "length_guidelines": "2-3 pages",
            "is_active": True,
        },
        {
            "name": "US Tech Fullstack",
            "language": "en",
            "industry": "tech",
            "description": "US market style for fullstack developers",
            "section_order": "Header, Professional Summary, Work Experience, Education, Skills",
            "formatting_rules": "1-2 pages, no photo, full-stack focus, metrics-driven",
            "style_guidelines": "Emphasize full-stack capabilities, include both frontend and backend achievements",
            "ats_keywords": "React, Vue, Angular, Python, Node.js, PostgreSQL, MongoDB, Docker, AWS",
            "tone_guidance": "Professional, results-oriented, concise",
            "length_guidelines": "1-2 pages",
            "is_active": True,
        },
        # Tech Industry - GPT Engineer
        {
            "name": "Russian Tech GPT Engineer",
            "language": "ru",
            "industry": "tech",
            "description": "Russian market style for GPT/AI engineers",
            "section_order": "Personal Info (with photo), Summary, Work Experience, Education, Skills, Languages",
            "formatting_rules": "2-3 pages, formal tone, AI/ML focus, research experience",
            "style_guidelines": "Highlight AI/ML projects, prompt engineering, LLM experience, research background",
            "ats_keywords": "GPT, LLM, AI, машинное обучение, prompt engineering, OpenAI, LangChain",
            "tone_guidance": "Formal, technical, research-oriented",
            "length_guidelines": "2-3 pages",
            "is_active": True,
        },
        {
            "name": "US Tech GPT Engineer",
            "language": "en",
            "industry": "tech",
            "description": "US market style for GPT/AI engineers",
            "section_order": "Header, Professional Summary, Work Experience, Education, Skills",
            "formatting_rules": "1-2 pages, no photo, AI/ML focus, project-based",
            "style_guidelines": "Emphasize AI projects, prompt engineering skills, LLM experience, measurable impact",
            "ats_keywords": "GPT, LLM, AI, machine learning, prompt engineering, OpenAI, LangChain, transformers",
            "tone_guidance": "Professional, technical, achievement-focused",
            "length_guidelines": "1-2 pages",
            "is_active": True,
        },
        # Finance Industry
        {
            "name": "Russian Finance",
            "language": "ru",
            "industry": "finance",
            "description": "Russian market style for finance professionals",
            "section_order": "Personal Info (with photo), Summary, Work Experience, Education, Skills, Certifications, Languages",
            "formatting_rules": "2-3 pages, formal tone, professional photo, emphasize certifications and qualifications",
            "style_guidelines": "Highlight financial analysis, risk management, regulatory compliance, quantitative skills",
            "ats_keywords": "финансовый анализ, риск-менеджмент, CFA, FRM, Excel, Bloomberg, SQL",
            "tone_guidance": "Formal, precise, detail-oriented",
            "length_guidelines": "2-3 pages",
            "is_active": True,
        },
        {
            "name": "US Finance",
            "language": "en",
            "industry": "finance",
            "description": "US market style for finance professionals",
            "section_order": "Header, Professional Summary, Work Experience, Education, Skills, Certifications",
            "formatting_rules": "1-2 pages, no photo, quantitative focus, results-driven",
            "style_guidelines": "Emphasize financial modeling, analysis, ROI, revenue impact, certifications",
            "ats_keywords": "Financial analysis, risk management, CFA, FRM, Excel, Bloomberg, SQL, Python",
            "tone_guidance": "Professional, analytical, results-focused",
            "length_guidelines": "1-2 pages",
            "is_active": True,
        },
        # Consulting Industry
        {
            "name": "Russian Consulting",
            "language": "ru",
            "industry": "consulting",
            "description": "Russian market style for consultants",
            "section_order": "Personal Info (with photo), Summary, Work Experience, Education, Skills, Languages, Projects",
            "formatting_rules": "2-3 pages, formal tone, professional photo, emphasize client projects and outcomes",
            "style_guidelines": "Highlight client engagements, problem-solving, strategic thinking, industry expertise",
            "ats_keywords": "консалтинг, стратегия, управление проектами, бизнес-анализ, клиентские проекты",
            "tone_guidance": "Formal, strategic, client-focused",
            "length_guidelines": "2-3 pages",
            "is_active": True,
        },
        {
            "name": "US Consulting",
            "language": "en",
            "industry": "consulting",
            "description": "US market style for consultants",
            "section_order": "Header, Professional Summary, Work Experience, Education, Skills, Projects",
            "formatting_rules": "1-2 pages, no photo, client-focused, impact-driven",
            "style_guidelines": "Emphasize client impact, problem-solving, strategic initiatives, measurable outcomes",
            "ats_keywords": "Consulting, strategy, project management, business analysis, client engagement, McKinsey, BCG",
            "tone_guidance": "Professional, strategic, results-oriented",
            "length_guidelines": "1-2 pages",
            "is_active": True,
        },
        # Healthcare Industry
        {
            "name": "Russian Healthcare",
            "language": "ru",
            "industry": "healthcare",
            "description": "Russian market style for healthcare professionals",
            "section_order": "Personal Info (with photo), Summary, Work Experience, Education, Certifications, Skills, Languages",
            "formatting_rules": "2-3 pages, formal tone, professional photo, emphasize licenses and certifications",
            "style_guidelines": "Highlight clinical experience, patient care, medical procedures, compliance, certifications",
            "ats_keywords": "клиническая практика, пациенты, медицинские процедуры, лицензия, сертификация",
            "tone_guidance": "Formal, compassionate, detail-oriented",
            "length_guidelines": "2-3 pages",
            "is_active": True,
        },
        {
            "name": "US Healthcare",
            "language": "en",
            "industry": "healthcare",
            "description": "US market style for healthcare professionals",
            "section_order": "Header, Professional Summary, Work Experience, Education, Licenses/Certifications, Skills",
            "formatting_rules": "1-2 pages, no photo, patient-focused, outcome-oriented",
            "style_guidelines": "Emphasize patient outcomes, clinical experience, quality metrics, licenses, certifications",
            "ats_keywords": "Patient care, clinical experience, medical procedures, license, certification, HIPAA, EMR",
            "tone_guidance": "Professional, compassionate, outcome-focused",
            "length_guidelines": "1-2 pages",
            "is_active": True,
        },
    ]

    # Check if presets already exist
    existing = db.execute(select(StylePreset)).scalars().all()
    if existing:
        # Presets already initialized
        return

    # Create default presets
    for preset_data in default_presets:
        preset = StylePreset(**preset_data)
        db.add(preset)

    db.commit()

