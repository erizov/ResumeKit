"""
End-to-end tests for real resume tailoring with actual job postings.

These tests:
1. Upload ResumeEugeneRizov.docx
2. Fetch real job posting URLs
3. Generate tailored resumes in Russian/English
4. Save output as DOCX files to output/ directory

To run with real OpenAI API:
    RESUMEKIT_USE_OPENAI=1 OPENAI_API_KEY=your-key pytest tests/e2e/test_real_resume_tailoring.py -v
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

# Enable OpenAI for these tests
os.environ["RESUMEKIT_USE_OPENAI"] = "1"

# Maximum number of output folders to keep
MAX_OUTPUT_FOLDERS = 9


@pytest.fixture(autouse=True, scope="module")
def _ensure_tables():
    """
    Ensure database tables exist before running tests.
    """
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    """
    Test client fixture.
    """
    return TestClient(app)


def cleanup_old_output_folders(base_output_dir: Path) -> None:
    """
    Remove old output folders, keeping only the MAX_OUTPUT_FOLDERS most recent.
    
    Args:
        base_output_dir: Base output directory containing timestamped folders
    """
    if not base_output_dir.exists():
        return
    
    # Find all timestamped folders (format: yyyymmdd.hh.mm.ss)
    timestamp_folders = []
    pattern = re.compile(r"^\d{8}\.\d{2}\.\d{2}\.\d{2}$")
    
    for item in base_output_dir.iterdir():
        if item.is_dir() and pattern.match(item.name):
            timestamp_folders.append(item)
    
    # Sort by modification time (newest first)
    timestamp_folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Remove folders beyond the limit
    if len(timestamp_folders) > MAX_OUTPUT_FOLDERS:
        for folder in timestamp_folders[MAX_OUTPUT_FOLDERS:]:
            print(f"Removing old output folder: {folder}")
            shutil.rmtree(folder)


@pytest.fixture(scope="session", autouse=True)
def cleanup_output_folders():
    """
    Cleanup old output folders before and after test session.
    """
    base_output_dir = Path("output")
    base_output_dir.mkdir(exist_ok=True)
    
    # Cleanup before tests
    cleanup_old_output_folders(base_output_dir)
    
    yield
    
    # Cleanup after tests
    cleanup_old_output_folders(base_output_dir)


@pytest.fixture
def output_dir():
    """
    Create timestamped output directory for test results.
    
    Format: output/yyyymmdd.hh.mm.ss
    """
    base_output_dir = Path("output")
    base_output_dir.mkdir(exist_ok=True)
    
    # Create timestamped folder
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d.%H.%M.%S")
    output_path = base_output_dir / timestamp
    output_path.mkdir(exist_ok=True)
    
    print(f"\n📁 Created output folder: {output_path}")
    
    return output_path


@pytest.fixture
def resume_file():
    """
    Get path to the resume file.
    """
    resume_path = Path("ResumeEugeneRizov.docx")
    if not resume_path.exists():
        pytest.skip(f"Resume file not found: {resume_path}")
    return resume_path


# Real job posting URLs for testing
# These are example URLs - replace with actual job posting URLs
# Format: hh.ru uses /vacancy/{id}, LinkedIn uses /jobs/view/{id}
JOB_URLS = {
    "russian_backend": None,  # Set to actual URL or None to use sample text
    "english_backend": None,  # Set to actual URL or None to use sample text
}


def fetch_job_description(client: TestClient, url: str | None) -> str:
    """
    Fetch job description from URL or return None if URL is not provided.
    
    Args:
        client: Test client
        url: Job posting URL
        
    Returns:
        Job description text or empty string if URL is None
    """
    if not url:
        return ""
    
    try:
        response = client.post("/api/job/fetch", json={"url": url})
        if response.status_code == 200:
            result = response.json()
            return result.get("text", "")
    except Exception as e:
        print(f"Warning: Failed to fetch job from URL {url}: {e}")
    
    return ""


def test_russian_job_posting_tailoring(
    client: TestClient, resume_file: Path, output_dir: Path
) -> None:
    """
    E2E test: Upload resume, fetch Russian job posting, generate Russian resume.

    This test:
    1. Uploads ResumeEugeneRizov.docx
    2. Fetches a real Russian job posting URL (backend/Java/GPT engineer)
    3. Generates tailored resume in Russian
    4. Saves output as DOCX to output/ResumeEugeneRizovRussian{JobID}.docx
    """
    # Check if OpenAI is configured (required for real tailoring)
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set - skipping real LLM test")

    # Step 1: Fetch job description from URL or use sample
    job_url = JOB_URLS.get("russian_backend")
    russian_job_description = fetch_job_description(client, job_url)
    
    # If URL fetch failed or URL not provided, use sample job description
    if not russian_job_description:
        russian_job_description = """
Требуется Backend разработчик

Обязанности:
- Разработка серверной части веб-приложений
- Работа с базами данных (PostgreSQL, MongoDB)
- Разработка REST API
- Оптимизация производительности

Требования:
- Опыт работы с Python/FastAPI или Java/Spring Boot
- Знание SQL и NoSQL баз данных
- Опыт работы с Docker и Kubernetes
- Понимание микросервисной архитектуры

Будет плюсом:
- Опыт с Redis, RabbitMQ, Kafka
- Знание CI/CD процессов
"""

    # Step 2: Generate tailored resume
    with open(resume_file, "rb") as f:
        response = client.post(
            "/api/recommend",
            files={"resume_file": ("ResumeEugeneRizov.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={
                "job_description": russian_job_description,
                "languages": "ru",
                "targets": "backend",
                "aggressiveness": "2",
            },
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    result = response.json()
    assert "resumes" in result
    assert len(result["resumes"]) > 0

    # Find Russian backend resume
    russian_resume = None
    for resume in result["resumes"]:
        if resume["language"] == "ru" and resume["target"] == "backend":
            russian_resume = resume
            break

    assert russian_resume is not None, "Russian backend resume not found in results"
    assert russian_resume["id"] is not None, "Resume ID should be set"

    resume_id = russian_resume["id"]

    # Step 3: Download as DOCX
    docx_response = client.get(f"/api/tailor/{resume_id}/docx")
    assert docx_response.status_code == 200, f"Expected 200, got {docx_response.status_code}"
    assert docx_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )

    # Step 4: Save to output directory
    job_id = str(resume_id)  # Use resume ID as job ID
    output_filename = f"ResumeEugeneRizovRussian{job_id}.docx"
    output_path = output_dir / output_filename

    with open(output_path, "wb") as f:
        f.write(docx_response.content)

    assert output_path.exists(), f"Output file not created: {output_path}"
    assert output_path.stat().st_size > 0, "Output file is empty"

    # Step 5: Save original job posting
    job_posting_filename = f"JobPostingRussian{job_id}.txt"
    job_posting_path = output_dir / job_posting_filename
    with open(job_posting_path, "w", encoding="utf-8") as f:
        f.write(russian_job_description)

    assert job_posting_path.exists(), f"Job posting file not created: {job_posting_path}"

    print(f"\n✅ Russian resume saved to: {output_path}")
    print(f"✅ Russian job posting saved to: {job_posting_path}")


def test_english_job_posting_tailoring(
    client: TestClient, resume_file: Path, output_dir: Path
) -> None:
    """
    E2E test: Upload resume, fetch English job posting, generate English resume.

    This test:
    1. Uploads ResumeEugeneRizov.docx
    2. Fetches a real English job posting URL (backend/Java/GPT engineer)
    3. Generates tailored resume in English
    4. Saves output as DOCX to output/ResumeEugeneRizovEnglish{JobID}.docx
    """
    # Check if OpenAI is configured (required for real tailoring)
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set - skipping real LLM test")

    # Step 1: Fetch job description from URL or use sample
    job_url = JOB_URLS.get("english_backend")
    english_job_description = fetch_job_description(client, job_url)
    
    # If URL fetch failed or URL not provided, use sample job description
    if not english_job_description:
        english_job_description = """
Backend Developer Position

Responsibilities:
- Develop server-side web applications
- Work with databases (PostgreSQL, MongoDB)
- Design and implement REST APIs
- Optimize application performance

Requirements:
- Experience with Python/FastAPI or Java/Spring Boot
- Knowledge of SQL and NoSQL databases
- Experience with Docker and Kubernetes
- Understanding of microservices architecture

Nice to have:
- Experience with Redis, RabbitMQ, Kafka
- Knowledge of CI/CD processes
"""

    # Step 1: Generate tailored resume
    with open(resume_file, "rb") as f:
        response = client.post(
            "/api/recommend",
            files={"resume_file": ("ResumeEugeneRizov.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={
                "job_description": english_job_description,
                "languages": "en",
                "targets": "backend",
                "aggressiveness": "2",
            },
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    result = response.json()
    assert "resumes" in result
    assert len(result["resumes"]) > 0

    # Find English backend resume
    english_resume = None
    for resume in result["resumes"]:
        if resume["language"] == "en" and resume["target"] == "backend":
            english_resume = resume
            break

    assert english_resume is not None, "English backend resume not found in results"
    assert english_resume["id"] is not None, "Resume ID should be set"

    resume_id = english_resume["id"]

    # Step 2: Download as DOCX
    docx_response = client.get(f"/api/tailor/{resume_id}/docx")
    assert docx_response.status_code == 200, f"Expected 200, got {docx_response.status_code}"
    assert docx_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )

    # Step 3: Save to output directory
    job_id = str(resume_id)  # Use resume ID as job ID
    output_filename = f"ResumeEugeneRizovEnglish{job_id}.docx"
    output_path = output_dir / output_filename

    with open(output_path, "wb") as f:
        f.write(docx_response.content)

    assert output_path.exists(), f"Output file not created: {output_path}"
    assert output_path.stat().st_size > 0, "Output file is empty"

    # Step 4: Save original job posting
    job_posting_filename = f"JobPostingEnglish{job_id}.txt"
    job_posting_path = output_dir / job_posting_filename
    with open(job_posting_path, "w", encoding="utf-8") as f:
        f.write(english_job_description)

    assert job_posting_path.exists(), f"Job posting file not created: {job_posting_path}"

    print(f"\n✅ English resume saved to: {output_path}")
    print(f"✅ English job posting saved to: {job_posting_path}")

