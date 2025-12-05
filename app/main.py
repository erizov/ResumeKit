"""
Main application entrypoint for the ResumeKit FastAPI backend.

The MVP exposes a minimal API surface for generating tailored resume
recommendations based on a user's resume and a target job description.
"""

# Load .env file FIRST, before any other imports that might use config
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure unbuffered output for real-time logging
os.environ.setdefault("PYTHONUNBUFFERED", "1")
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"[Main] Loaded .env from: {env_path.absolute()}")

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from .db import Base, engine, SessionLocal
from .routers import api_router
from .services.preset_service import initialize_default_presets
from .services.init_admin import init_admin_user
from .middleware.error_handler import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    user_friendly_exception_handler,
    general_exception_handler,
    UserFriendlyError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Ensures database tables exist on startup. For production deployments
    this can be replaced with Alembic migrations; for the MVP this keeps
    setup simple.
    """
    Base.metadata.create_all(bind=engine)
    
    # Initialize default style presets and admin user
    db = SessionLocal()
    try:
        initialize_default_presets(db)
        init_admin_user(db)
    except Exception as e:
        print(f"Warning: Failed to initialize defaults: {e}")
    finally:
        db.close()
    
    yield


# Initialize rate limiter (in-memory for MVP, can use Redis in production)
limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    """
    app = FastAPI(
        title="ResumeKit API",
        version="0.1.0",
        description=(
            "API for tailoring resumes and cover letters to specific "
            "job descriptions using LLMs."
        ),
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add error handlers for user-friendly error messages
    app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    app.add_exception_handler(
        SQLAlchemyError, sqlalchemy_exception_handler
    )
    app.add_exception_handler(
        UserFriendlyError, user_friendly_exception_handler
    )
    app.add_exception_handler(Exception, general_exception_handler)

    # Health check at root level (no /api prefix)
    from .routes import health
    app.include_router(health.router)

    # API routes with /api prefix
    app.include_router(api_router, prefix="/api")

    # Root endpoint - redirect to docs
    @app.get("/")
    def root():
        """
        Root endpoint - provides API information and links.
        """
        return {
            "message": "ResumeKit API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
            "api_base": "/api",
        }

    return app


app = create_app()


