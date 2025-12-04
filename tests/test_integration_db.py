"""
Database integration tests for ResumeKit models and relationships.

These tests verify CRUD operations, foreign key relationships,
and query performance.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from app.models import Base, BaseResume, JobPosting, TailoredResume


@pytest.fixture(scope="function")
def db_session():
    """
    Create a test database session.

    Uses a fresh in-memory SQLite database for each test.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_create_base_resume(db_session: Session) -> None:
    """Test creating a BaseResume record."""
    resume = BaseResume(text="Sample resume text.")
    db_session.add(resume)
    db_session.commit()

    assert resume.id is not None
    assert resume.created_at is not None
    assert isinstance(resume.created_at, datetime)
    assert resume.text == "Sample resume text."


def test_create_job_posting(db_session: Session) -> None:
    """Test creating a JobPosting record."""
    job = JobPosting(text="Sample job description.")
    db_session.add(job)
    db_session.commit()

    assert job.id is not None
    assert job.created_at is not None
    assert isinstance(job.created_at, datetime)
    assert job.text == "Sample job description."


def test_create_tailored_resume_with_relationships(
    db_session: Session,
) -> None:
    """Test creating TailoredResume with foreign key relationships."""
    base_resume = BaseResume(text="Base resume.")
    job_posting = JobPosting(text="Job posting.")
    db_session.add(base_resume)
    db_session.add(job_posting)
    db_session.flush()

    tailored = TailoredResume(
        language="en",
        target="backend",
        content="Tailored content.",
        notes="Generated notes.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    db_session.add(tailored)
    db_session.commit()

    assert tailored.id is not None
    assert tailored.base_resume_id == base_resume.id
    assert tailored.job_posting_id == job_posting.id
    assert tailored.base_resume == base_resume
    assert tailored.job_posting == job_posting


def test_cascade_delete_base_resume(db_session: Session) -> None:
    """Test that deleting BaseResume cascades to TailoredResume."""
    base_resume = BaseResume(text="Base resume.")
    job_posting = JobPosting(text="Job posting.")
    db_session.add(base_resume)
    db_session.add(job_posting)
    db_session.flush()

    tailored = TailoredResume(
        language="en",
        target="backend",
        content="Content.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    db_session.add(tailored)
    db_session.commit()

    tailored_id = tailored.id

    # Delete base resume
    db_session.delete(base_resume)
    db_session.commit()

    # Tailored resume should be deleted
    deleted = db_session.get(TailoredResume, tailored_id)
    assert deleted is None


def test_cascade_delete_job_posting(db_session: Session) -> None:
    """Test that deleting JobPosting cascades to TailoredResume."""
    base_resume = BaseResume(text="Base resume.")
    job_posting = JobPosting(text="Job posting.")
    db_session.add(base_resume)
    db_session.add(job_posting)
    db_session.flush()

    tailored = TailoredResume(
        language="en",
        target="backend",
        content="Content.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    db_session.add(tailored)
    db_session.commit()

    tailored_id = tailored.id

    # Delete job posting
    db_session.delete(job_posting)
    db_session.commit()

    # Tailored resume should be deleted
    deleted = db_session.get(TailoredResume, tailored_id)
    assert deleted is None


def test_query_tailored_resumes_by_language(db_session: Session) -> None:
    """Test querying TailoredResume by language."""
    base_resume = BaseResume(text="Base.")
    job_posting = JobPosting(text="Job.")
    db_session.add(base_resume)
    db_session.add(job_posting)
    db_session.flush()

    tailored_en = TailoredResume(
        language="en",
        target="backend",
        content="English content.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    tailored_ru = TailoredResume(
        language="ru",
        target="backend",
        content="Russian content.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    db_session.add(tailored_en)
    db_session.add(tailored_ru)
    db_session.commit()

    # Query by language
    en_resumes = (
        db_session.query(TailoredResume)
        .filter(TailoredResume.language == "en")
        .all()
    )
    assert len(en_resumes) == 1
    assert en_resumes[0].language == "en"


def test_query_tailored_resumes_by_target(db_session: Session) -> None:
    """Test querying TailoredResume by target."""
    base_resume = BaseResume(text="Base.")
    job_posting = JobPosting(text="Job.")
    db_session.add(base_resume)
    db_session.add(job_posting)
    db_session.flush()

    tailored_backend = TailoredResume(
        language="en",
        target="backend",
        content="Backend content.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    tailored_fullstack = TailoredResume(
        language="en",
        target="fullstack",
        content="Fullstack content.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    db_session.add(tailored_backend)
    db_session.add(tailored_fullstack)
    db_session.commit()

    # Query by target
    backend_resumes = (
        db_session.query(TailoredResume)
        .filter(TailoredResume.target == "backend")
        .all()
    )
    assert len(backend_resumes) == 1
    assert backend_resumes[0].target == "backend"


def test_pagination_query(db_session: Session) -> None:
    """Test pagination queries on TailoredResume."""
    base_resume = BaseResume(text="Base.")
    job_posting = JobPosting(text="Job.")
    db_session.add(base_resume)
    db_session.add(job_posting)
    db_session.flush()

    # Create multiple tailored resumes
    for i in range(5):
        tailored = TailoredResume(
            language="en",
            target="backend",
            content=f"Content {i}.",
            base_resume_id=base_resume.id,
            job_posting_id=job_posting.id,
        )
        db_session.add(tailored)
    db_session.commit()

    # Test pagination
    page1 = (
        db_session.query(TailoredResume)
        .order_by(TailoredResume.id)
        .limit(2)
        .offset(0)
        .all()
    )
    page2 = (
        db_session.query(TailoredResume)
        .order_by(TailoredResume.id)
        .limit(2)
        .offset(2)
        .all()
    )

    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0].id != page2[0].id


def test_relationship_access(db_session: Session) -> None:
    """Test accessing related objects via relationships."""
    base_resume = BaseResume(text="Base resume text.")
    job_posting = JobPosting(text="Job posting text.")
    db_session.add(base_resume)
    db_session.add(job_posting)
    db_session.flush()

    tailored = TailoredResume(
        language="en",
        target="backend",
        content="Tailored content.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    db_session.add(tailored)
    db_session.commit()

    # Access via relationship
    assert tailored.base_resume.text == "Base resume text."
    assert tailored.job_posting.text == "Job posting text."

    # Access reverse relationship
    assert tailored in base_resume.tailored_resumes
    assert tailored in job_posting.tailored_resumes


def test_update_tailored_resume(db_session: Session) -> None:
    """Test updating a TailoredResume record."""
    base_resume = BaseResume(text="Base.")
    job_posting = JobPosting(text="Job.")
    db_session.add(base_resume)
    db_session.add(job_posting)
    db_session.flush()

    tailored = TailoredResume(
        language="en",
        target="backend",
        content="Original content.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    db_session.add(tailored)
    db_session.commit()

    # Update
    tailored.content = "Updated content."
    tailored.notes = "Updated notes."
    db_session.commit()

    # Verify update
    updated = db_session.get(TailoredResume, tailored.id)
    assert updated is not None
    assert updated.content == "Updated content."
    assert updated.notes == "Updated notes."


def test_timestamp_ordering(db_session: Session) -> None:
    """Test that created_at timestamps are set correctly."""
    base_resume = BaseResume(text="Base.")
    job_posting = JobPosting(text="Job.")
    db_session.add(base_resume)
    db_session.add(job_posting)
    db_session.flush()

    before = datetime.now(UTC).replace(tzinfo=None)

    tailored = TailoredResume(
        language="en",
        target="backend",
        content="Content.",
        base_resume_id=base_resume.id,
        job_posting_id=job_posting.id,
    )
    db_session.add(tailored)
    db_session.commit()

    after = datetime.now(UTC).replace(tzinfo=None)

    # SQLite stores naive datetimes, so compare as naive
    created_at_naive = tailored.created_at.replace(
        tzinfo=None
    ) if tailored.created_at.tzinfo else tailored.created_at
    assert before <= created_at_naive <= after

