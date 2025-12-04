"""
SQLAlchemy ORM models for persisting resumes and job descriptions.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    """
    User account for authentication and authorization.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    base_resumes: Mapped[list["BaseResume"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    job_postings: Mapped[list["JobPosting"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class BaseResume(Base):
    """
    Original resume text uploaded or provided by the user.
    """

    __tablename__ = "base_resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    text: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    user: Mapped["User | None"] = relationship(back_populates="base_resumes")
    tailored_resumes: Mapped[list["TailoredResume"]] = relationship(
        back_populates="base_resume",
        cascade="all, delete-orphan",
    )


class JobPosting(Base):
    """
    Job description text used for tailoring.
    """

    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    text: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    user: Mapped["User | None"] = relationship(back_populates="job_postings")
    tailored_resumes: Mapped[list["TailoredResume"]] = relationship(
        back_populates="job_posting",
        cascade="all, delete-orphan",
    )


class TailoredResume(Base):
    """
    Tailored resume variant for a specific language and target role.
    """

    __tablename__ = "tailored_resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    language: Mapped[str] = mapped_column(String, index=True)
    target: Mapped[str] = mapped_column(String, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    base_resume_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("base_resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_posting_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
    )

    base_resume: Mapped[BaseResume] = relationship(
        back_populates="tailored_resumes"
    )
    job_posting: Mapped[JobPosting] = relationship(
        back_populates="tailored_resumes"
    )

    cover_letters: Mapped[list["TailoredCoverLetter"]] = relationship(
        back_populates="tailored_resume",
        cascade="all, delete-orphan",
    )


class TailoredCoverLetter(Base):
    """
    Cover letter generated for a specific tailored resume.
    """

    __tablename__ = "tailored_cover_letters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    text: Mapped[str] = mapped_column(String, nullable=False)

    tailored_resume_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tailored_resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tailored_resume: Mapped[TailoredResume] = relationship(
        back_populates="cover_letters"
    )


class StylePreset(Base):
    """
    Style preset for resume tailoring based on language and industry.
    """

    __tablename__ = "style_presets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    language: Mapped[str] = mapped_column(String, nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # Preset configuration (JSON-like structure stored as text)
    section_order: Mapped[str | None] = mapped_column(Text, nullable=True)
    formatting_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    style_guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)
    ats_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    length_guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(default=True, index=True)


