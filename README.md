## ResumeKit – Tailored Resume MVP

Minimal backend + frontend to tailor a resume to a specific job
description using FastAPI, OpenAI, and a React/MUI frontend.

### Project structure

- **Backend** – FastAPI app in `app/`
  - `app/main.py` – FastAPI app factory and entrypoint.
  - `app/routes/recommend.py` – `POST /api/recommend` endpoint.
  - `app/services/` – parsing and tailoring services.
  - `app/schemas.py` – Pydantic models and enums.
- **Frontend** – React + Vite + MUI + React Router app in `frontend/`
  - `frontend/src/App.tsx` – main app with routing setup
  - `frontend/src/components/Layout.tsx` – layout with navigation bar
  - `frontend/src/pages/HomePage.tsx` – main form to generate tailored resumes
  - `frontend/src/pages/HistoryPage.tsx` – list of all generated resumes
  - `frontend/src/pages/DetailPage.tsx` – detailed view with PDF download

### How to run things locally (once you install deps)

#### 1. Backend – install and test

From the project root:

```bash
python -m venv .venv
.\.venv\Scripts\activate  # on Windows PowerShell
pip install -r requirements.txt

pytest -q
```

#### 2. Backend – run development server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, with:

- `POST /api/recommend` – main tailoring endpoint (rate limited: 10/hour).
- `GET /api/history` – list of generated tailored resumes.
- `GET /api/tailor/{id}` – detailed view for a specific tailored resume.
- `GET /api/tailor/{id}/coverage` – keyword coverage analysis (matched/missing skills, score).
- `GET /api/tailor/{id}/pdf` – download tailored resume as PDF.
- `GET /api/tailor/{id}/docx` – download tailored resume as DOCX.
- `POST /api/tailor/{id}/cover-letter` – generate cover letter (rate limited: 5/hour).
- `GET /api/tailor/{id}/cover-letter` – retrieve existing cover letter.
- `GET /api/metrics` – basic application statistics.
- `POST /api/job/fetch` – fetch and parse job description from URL.
- `GET /health` – health check endpoint.
- `POST /api/auth/signup` – user registration.
- `POST /api/auth/login` – user authentication (returns JWT token).
- `GET /api/auth/me` – get current user info (requires authentication).
- `POST /api/resume/parse` – parse resume into structured format (name, experience, skills, etc.).

#### 3. Frontend – install and run dev server

From the `frontend/` directory:

```bash
npm install
npm run dev
```

By default Vite runs on `http://localhost:5173` and proxies `/api`
to `http://localhost:8000`, so the React UI can call the FastAPI
backend without CORS issues.

### Enabling real OpenAI tailoring

By default the backend uses a deterministic stub implementation for
`/api/recommend` so tests are fast and reproducible.

To enable OpenAI-backed tailoring at runtime:

```bash
setx OPENAI_API_KEY "sk-..."         # or export on Unix
setx RESUMEKIT_USE_OPENAI "1"
```

Then restart the backend. The same `/api/recommend` endpoint will
start using OpenAI (`gpt-4.1-mini`) behind the scenes while the tests
continue to run against the stub by default.

### Running Tests

#### Backend Tests

All backend tests use `pytest` and are located in the `tests/` directory.

**Quick test run:**
```bash
# Run all tests (quiet mode)
pytest -q

# Run all tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_recommend_endpoint.py

# Run specific test function
pytest tests/test_recommend_endpoint.py::test_recommend_basic
```

**Test categories:**

1. **Unit tests** – Test individual components:
   - `test_recommend_endpoint.py` – Main recommendation endpoint
   - `test_recommend_file_upload.py` – File upload handling
   - `test_job_fetch.py` – Job URL fetching
   - `test_resume_parse.py` – Resume parsing endpoint
   - `test_keyword_coverage.py` – Keyword coverage analysis
   - `test_pdf_export.py` – PDF generation

2. **Integration tests** – Test full workflows:
   - `test_integration_api.py` – End-to-end API flows
   - `test_integration_db.py` – Database operations and relationships
   - `test_history_and_detail.py` – History and detail endpoints

3. **OpenAI integration tests** (optional):
   - `test_integration_openai.py` – Real OpenAI API calls
   - These tests are skipped if `OPENAI_API_KEY` is not set
   - To run: Set `OPENAI_API_KEY` and `RESUMEKIT_USE_OPENAI=1`

**Test database:**

Tests use an in-memory SQLite database by default (configured via `DATABASE_URL`).
Each test gets a clean database state, so tests can run in any order.

**Running tests with coverage:**

```bash
# Install coverage tool (if not already installed)
pip install pytest-cov

# Run tests with coverage report
pytest --cov=app --cov-report=html

# View HTML report
# Open htmlcov/index.html in your browser
```

**Test output:**

- `-q` (quiet): Shows only dots for passed tests and summary
- `-v` (verbose): Shows each test name and result
- `-s`: Shows print statements and output
- `-x`: Stop on first failure

**Example test run:**
```bash
$ pytest -q
....................ssss.....................s..
43 passed, 5 skipped, 1 warning in 15.90s

# Or with verbose output:
$ pytest -v
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-7.4.3
collected 48 items

tests/test_recommend_endpoint.py::test_recommend_basic PASSED
tests/test_recommend_endpoint.py::test_recommend_with_file PASSED
...
tests/test_integration_api.py::test_full_flow PASSED
tests/test_integration_db.py::test_cascade_delete PASSED
tests/test_integration_openai.py::test_openai_tailoring SKIPPED
...

============================= 43 passed, 5 skipped in 15.90s ===================
```

**Skipped tests:**

Some tests are skipped under certain conditions:
- OpenAI integration tests: Skipped if `OPENAI_API_KEY` is not set
- These are marked with `@pytest.mark.skipif` decorators

**Troubleshooting:**

- **Import errors**: Make sure you're in the project root and virtual environment is activated
- **Database errors**: Tests create tables automatically; ensure SQLite is available
- **OpenAI tests failing**: Check that `OPENAI_API_KEY` is set correctly and API is accessible

#### E2E Tests for Real Resume Tailoring

End-to-end tests that use real resume files and job postings:
- `tests/e2e/test_real_resume_tailoring.py` – Tests with actual resume file
  - Uploads `ResumeEugeneRizov.docx`
  - Generates tailored resumes in Russian and English
  - Saves output as DOCX files to `output/` directory

**To run E2E tests with real OpenAI:**
```bash
# Windows PowerShell
$env:RESUMEKIT_USE_OPENAI="1"
pytest tests/e2e/test_real_resume_tailoring.py -v

# Linux/Mac
RESUMEKIT_USE_OPENAI=1 pytest tests/e2e/test_real_resume_tailoring.py -v
```

**Note:** These tests require `OPENAI_API_KEY` to be set and will use real OpenAI API calls.

#### Frontend Tests

Frontend tests are not yet implemented. Planned:
- Unit tests for React components (Jest + React Testing Library)
- Integration tests for API client
- E2E tests with Playwright (see `development_roadmap.md`)

### Database Migrations

The project uses Alembic for database schema versioning.

**Initial setup:**
```bash
# Alembic is already initialized
# Run migrations to create/update database schema
alembic upgrade head
```

**Creating new migrations:**
```bash
# After modifying models in app/models.py
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

**Rollback:**
```bash
# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

### Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for detailed deployment instructions.

**Quick start with Docker Compose:**
```bash
# Start all services (PostgreSQL, backend, frontend)
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f
```

**Production deployment:**
- Backend: Docker container or direct Python deployment
- Frontend: Static build deployed to CDN or nginx
- Database: PostgreSQL with automated backups
- See `DEPLOYMENT.md` for complete guide

### Development Roadmap

See [`development_roadmap.md`](development_roadmap.md) for planned
frontend improvements, additional backend features, and integration tests.

**Current Status:**
- ✅ Backend MVP with `/api/recommend`, `/api/history`, `/api/tailor/{id}`
- ✅ PDF export: `GET /api/tailor/{id}/pdf` generates downloadable PDFs
- ✅ DOCX export: `GET /api/tailor/{id}/docx` generates downloadable DOCX files
- ✅ Cover letter generation: `POST /api/tailor/{id}/cover-letter` with OpenAI
- ✅ Rate limiting: Applied to expensive endpoints (configurable via `RATE_LIMIT_ENABLED`)
- ✅ Metrics: `GET /api/metrics` provides basic statistics
- ✅ Health checks: `GET /health` for monitoring
- ✅ Authentication: JWT-based auth with signup/login endpoints
- ✅ Database migrations: Alembic configured for schema versioning
- ✅ Deployment: Docker and docker-compose configuration ready
- ✅ Integration tests: API flow tests, database tests, contract tests, optional OpenAI tests
- ✅ E2E tests: Playwright test suite configured
- ✅ RAG (Retrieval-Augmented Generation): Market-specific best practices integration for enhanced tailoring
- ✅ Backend features: Job URL fetching, structured parsing, keyword coverage, PDF export, cover letters, rate limiting, metrics, RAG
- ✅ Frontend improvements: History page, detail view, routing with React Router
- ✅ Frontend UX: Copy to clipboard, job URL fetching in form, keyword coverage visualization
- ✅ Frontend polish: Drag-and-drop file upload, diff view (side-by-side/unified), responsive design

The roadmap is organized by priority and includes:
- Frontend: History page, detail view, routing, keyword coverage, export ✅
- Backend: Job URL fetching, structured parsing, PDF export, cover letters ✅
- Integration tests: ✅ API flow tests (done), ✅ Contract tests (done), ✅ E2E tests with Playwright (configured)
- Production readiness: ✅ Authentication, ✅ Migrations, ✅ Deployment configuration


