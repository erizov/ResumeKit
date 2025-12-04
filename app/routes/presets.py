"""
API endpoints for style preset management.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import StylePreset
from ..schemas import StylePresetCreate, StylePresetResponse

router = APIRouter()


@router.get("/presets", response_model=List[StylePresetResponse])
def get_presets(
    language: str | None = Query(None, description="Filter by language"),
    industry: str | None = Query(None, description="Filter by industry"),
    active_only: bool = Query(True, description="Only return active presets"),
    db: Session = Depends(get_db),
) -> List[StylePresetResponse]:
    """
    Get all style presets, optionally filtered by language and industry.
    """
    from ..services.preset_service import get_all_presets, get_preset_by_language_and_industry

    if language and industry:
        preset = get_preset_by_language_and_industry(db, language, industry)
        if preset:
            return [StylePresetResponse.model_validate(preset)]
        return []

    presets = get_all_presets(db, active_only=active_only)

    # Apply filters
    if language:
        presets = [p for p in presets if p.language == language]
    if industry:
        presets = [p for p in presets if p.industry == industry]

    return [StylePresetResponse.model_validate(p) for p in presets]


@router.post("/presets", response_model=StylePresetResponse, status_code=201)
def create_preset(
    preset_data: StylePresetCreate,
    db: Session = Depends(get_db),
) -> StylePresetResponse:
    """
    Create a new style preset.
    """
    from ..services.preset_service import create_preset

    preset = create_preset(db, preset_data.model_dump())
    return StylePresetResponse.model_validate(preset)


@router.get("/presets/{preset_id}", response_model=StylePresetResponse)
def get_preset(
    preset_id: int,
    db: Session = Depends(get_db),
) -> StylePresetResponse:
    """
    Get a specific style preset by ID.
    """
    preset = db.get(StylePreset, preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Style preset not found")
    return StylePresetResponse.model_validate(preset)

