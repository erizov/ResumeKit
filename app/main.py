"""
Main application entrypoint for the ResumeKit FastAPI backend.

The MVP exposes a minimal API surface for generating tailored resume
recommendations based on a user's resume and a target job description.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .db import Base, engine, SessionLocal
from .routers import api_router
from .services.preset_service import initialize_default_presets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Ensures database tables exist on startup. For production deployments
    this can be replaced with Alembic migrations; for the MVP this keeps
    setup simple.
    """
    Base.metadata.create_all(bind=engine)
    
    # Initialize default style presets
    db = SessionLocal()
    try:
        initialize_default_presets(db)
    except Exception as e:
        print(f"Warning: Failed to initialize presets: {e}")
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

    # Configure rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Health check at root level (no /api prefix)
    from .routes import health
    app.include_router(health.router)

    # API routes with /api prefix
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()


