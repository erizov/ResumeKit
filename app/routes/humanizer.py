"""
Text humanization and AI detection endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..services.humanizer import check_ai_score, humanize_text


router = APIRouter()


class HumanizeRequest(BaseModel):
    """Request to humanize text."""

    text: str = Field(..., description="Text to humanize")
    language: str = Field(default="en", description="Language code (en, ru)")
    apply_variations: bool = Field(
        default=True, description="Apply random variations"
    )


class HumanizeResponse(BaseModel):
    """Response with humanized text."""

    original: str
    humanized: str
    ai_score_before: dict
    ai_score_after: dict


class AIScoreRequest(BaseModel):
    """Request to check AI score."""

    text: str = Field(..., description="Text to analyze")
    language: str = Field(default="en", description="Language code (en, ru)")


@router.post("/humanize", response_model=HumanizeResponse)
def humanize_text_endpoint(request: HumanizeRequest) -> HumanizeResponse:
    """
    Humanize text to reduce AI stigmas and make it more natural.

    This endpoint:
    - Replaces common AI buzzwords with natural alternatives
    - Adds natural variations (contractions, style)
    - Varies sentence structure
    - Reduces excessive enthusiasm markers

    Returns both original and humanized text with AI scores.
    """
    original = request.text
    score_before = check_ai_score(original, request.language)

    humanized = humanize_text(
        original,
        language=request.language,
        apply_variations=request.apply_variations,
    )

    score_after = check_ai_score(humanized, request.language)

    return HumanizeResponse(
        original=original,
        humanized=humanized,
        ai_score_before=score_before,
        ai_score_after=score_after,
    )


@router.post("/ai-score", response_model=dict)
def check_ai_score_endpoint(request: AIScoreRequest) -> dict:
    """
    Analyze text for AI detection patterns.

    Returns:
    - score: 0-100 (higher = more AI-like)
    - flags: List of detected AI patterns
    - suggestions: List of improvement suggestions
    - is_likely_ai: Boolean indicating if text is likely AI-generated
    """
    return check_ai_score(request.text, request.language)

