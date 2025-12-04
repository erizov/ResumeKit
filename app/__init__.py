"""
Application package for the ResumeKit FastAPI backend.

This module exposes the FastAPI application instance for ASGI servers.
"""

from .main import create_app

app = create_app()


