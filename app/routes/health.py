"""
Health check endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Status dictionary with "status" key set to "healthy" if database
        connection is successful, "unhealthy" otherwise.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception:
        return {"status": "unhealthy"}

