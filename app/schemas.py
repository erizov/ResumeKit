"""
Pydantic schemas and enums for the ResumeKit backend.
"""

from enum import Enum
from typing import List, Optional

from datetime import datetime
from pydantic import BaseModel, Field


class LanguageCode(str, Enum):
    """
    Supported language codes for tailored resumes.
    """

    EN = "en"
    RU = "ru"


class TargetRole(str, Enum):
    """
    Supported target roles for tailoring.
    """

    BACKEND = "backend"
    FULLSTACK = "fullstack"
    GPT_ENGINEER = "gpt_engineer"


class TailoredResume(BaseModel):
    """
    A single tailored resume variant for a language and target role.
    """

    id: int | None = None
    created_at: datetime | None = None
    language: LanguageCode
    target: TargetRole
    content: str
    notes: str | None = None


class RecommendOptions(BaseModel):
    """
    Options that influence how tailoring is performed.
    """

    languages: List[LanguageCode] = Field(
        default_factory=lambda: [LanguageCode.EN, LanguageCode.RU]
    )
    targets: List[TargetRole] = Field(
        default_factory=lambda: [TargetRole.BACKEND]
    )
    aggressiveness: int = Field(
        default=2,
        ge=1,
        le=3,
        description=(
            "How strongly to rewrite the resume. 1=minimal, 2=balanced, "
            "3=aggressive."
        ),
    )


class RecommendResult(BaseModel):
    """
    Result of tailoring a resume to one or more roles and languages.
    """

    resumes: List[TailoredResume]


class TailoredResumeSummary(BaseModel):
    """
    Summary representation of a tailored resume for history listings.
    """

    id: int
    created_at: datetime
    language: LanguageCode
    target: TargetRole


class TailoredResumeDetail(BaseModel):
    """
    Detailed representation of a tailored resume, including source texts.
    """

    id: int
    created_at: datetime
    language: LanguageCode
    target: TargetRole
    content: str
    notes: str | None = None
    base_resume_text: str
    job_description: str


class HistoryResponse(BaseModel):
    """
    Paginated list of tailored resumes.
    """

    items: List[TailoredResumeSummary]
    total: int


class JobFetchRequest(BaseModel):
    """
    Request to fetch a job description from a URL.
    """

    url: str = Field(..., description="URL of the job posting page")


class JobFetchResponse(BaseModel):
    """
    Response containing the extracted job description text.
    """

    url: str
    text: str
    success: bool = True


class ExperienceEntry(BaseModel):
    """
    A single work experience entry.
    """

    title: str
    company: str
    start_date: str | None = None
    end_date: str | None = None
    description: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    """
    A single education entry.
    """

    degree: str
    institution: str
    field_of_study: str | None = None
    graduation_date: str | None = None


class StructuredResume(BaseModel):
    """
    Structured representation of a resume parsed from text.
    """

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    summary: str | None = None
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[dict[str, str]] = Field(default_factory=list)


class ResumeParseResponse(BaseModel):
    """
    Response containing structured resume data.
    """

    text: str
    structured: StructuredResume
    success: bool = True


class KeywordCoverage(BaseModel):
    """
    Keyword coverage analysis between resume and job description.
    """

    matched: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0, description="Coverage score (0.0 to 1.0)")
    total_jd_keywords: int = 0
    total_resume_keywords: int = 0


class CoverLetterRequest(BaseModel):
    """
    Request to generate a cover letter for a tailored resume.
    """

    custom_instructions: str | None = Field(
        None, description="Optional custom instructions for the cover letter"
    )


class CoverLetterResponse(BaseModel):
    """
    Response containing the generated cover letter.
    """

    id: int
    created_at: datetime
    text: str
    tailored_resume_id: int
    version: int = 1


class CoverLetterListResponse(BaseModel):
    """
    Response containing multiple cover letter versions.
    """

    cover_letters: List[CoverLetterResponse]


class UserSignup(BaseModel):
    """
    Request schema for user signup.
    """

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")


class UserLogin(BaseModel):
    """
    Request schema for user login.
    """

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """
    Response schema for authentication token.
    """

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """
    Response schema for user information.
    """

    id: int
    email: str
    created_at: datetime


class StylePresetCreate(BaseModel):
    """
    Schema for creating a style preset.
    """

    name: str
    language: str
    industry: str
    description: Optional[str] = None
    section_order: Optional[str] = None
    formatting_rules: Optional[str] = None
    style_guidelines: Optional[str] = None
    ats_keywords: Optional[str] = None
    tone_guidance: Optional[str] = None
    length_guidelines: Optional[str] = None
    is_active: bool = True


class StylePresetResponse(BaseModel):
    """
    Schema for style preset response.
    """

    id: int
    created_at: datetime
    updated_at: datetime
    name: str
    language: str
    industry: str
    description: Optional[str] = None
    section_order: Optional[str] = None
    formatting_rules: Optional[str] = None
    style_guidelines: Optional[str] = None
    ats_keywords: Optional[str] = None
    tone_guidance: Optional[str] = None
    length_guidelines: Optional[str] = None
    is_active: bool


