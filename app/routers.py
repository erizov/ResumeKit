"""
Top-level API router for the ResumeKit backend.

This module groups versioned and feature-specific routers.
"""

from fastapi import APIRouter

from .routes import auth, cover_letter, health, history, job, metrics, presets, recommend, resume

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(recommend.router, tags=["recommend"])
api_router.include_router(history.router, tags=["history"])
api_router.include_router(job.router, prefix="/job", tags=["job"])
api_router.include_router(resume.router, prefix="/resume", tags=["resume"])
api_router.include_router(cover_letter.router, tags=["cover-letter"])
api_router.include_router(metrics.router, tags=["metrics"])
api_router.include_router(presets.router, tags=["presets"])


