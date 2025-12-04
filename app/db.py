"""
Database configuration and session management.

By default a local SQLite database is used for development and tests.
For production, configure the DATABASE_URL environment variable with a
PostgreSQL URL, for example:

    postgresql+psycopg2://user:password@localhost:5432/resumekit
"""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resumekit.db")


class Base(DeclarativeBase):
    """
    Base class for ORM models.
    """


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for FastAPI dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


