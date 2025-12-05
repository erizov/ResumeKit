## ResumeKit – Tailored Resume MVP

Minimal backend + frontend to tailor a resume to a specific job
description using FastAPI, OpenAI, and a React/MUI frontend.

### Quick Start

**Start both services:**
```bash
# PowerShell (Windows) - Opens separate windows with prefixed logs
.\start.ps1

# Alternative: Separate log windows (recommended)
.\start-logs.ps1

# Batch (Windows) - Opens separate windows
start.bat
```

**Stop both services:**
```bash
.\stop.ps1    # PowerShell
stop.bat      # Batch
```

**Restart both services:**
```bash
.\restart.ps1  # PowerShell
restart.bat    # Batch
```

**Log Format:**
- All logs are prefixed with `[Backend]` or `[Frontend]`
- Timestamps included: `[Backend] [HH:mm:ss] log message`
- Separate PowerShell/CMD windows for each service
- Error logs are also prefixed and visible in terminal

After starting, access:
- **Frontend**: http://localhost:5173 (with resume file chooser)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

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

pytest tests/test_humanizer.py tests/test_humanizer_russian.py -v --tb=short
```

#### 2. Backend – run development server

**Option A: Use convenience scripts (recommended)**

```bash
# PowerShell (Windows)
.\start.ps1      # Start both backend and frontend
.\stop.ps1       # Stop both services
.\restart.ps1    # Restart both services

# Batch (Windows)
start.bat        # Start both backend and frontend
stop.bat         # Stop both services
restart.bat      # Restart both services
```

**Option B: Manual start**

```bash
# Backend only
uvicorn app.main:app --reload

# Frontend only (in separate terminal)
cd frontend
npm run dev
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
- `GET /api/cover-letter/{id}/pdf` – download cover letter as PDF.
- `GET /api/metrics` – basic application statistics.
- `POST /api/job/fetch` – fetch and parse job description from URL.
- `GET /health` – health check endpoint.
- `POST /api/auth/signup` – user registration.
- `POST /api/auth/login` – user authentication (returns JWT token).
- `GET /api/auth/me` – get current user info (requires authentication).
- `POST /api/resume/parse` – parse resume into structured format (name, experience, skills, etc.).
- `POST /api/humanizer/humanize` – humanize text to reduce AI stigmas.
- `POST /api/humanizer/ai-score` – check AI detection score for text.

#### 3. Frontend – install and run dev server

From the `frontend/` directory:

```bash
npm install
npm run dev
```

By default Vite runs on `http://localhost:5173` and proxies `/api`
to `http://localhost:8000`, so the React UI can call the FastAPI
backend without CORS issues.

### Environment Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Authentication
AUTH_SECRET_KEY=your_secret_key_here
AUTH_TOKEN_EXPIRE_HOURS=10  # Session expiration in hours (default: 10)

# OpenAI (optional, for AI features)
OPENAI_API_KEY=sk-...
```

**Important:** 
- The `.env` file is gitignored. Never commit secrets to the repository.
- Session expiration is configurable via `AUTH_TOKEN_EXPIRE_HOURS` (default: 10 hours)
- Expired sessions automatically redirect users to the login page

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
   
   ```bash
   pytest tests/test_recommend_endpoint.py
   pytest tests/test_resume_parse.py
   pytest tests/test_pdf_export.py
   pytest tests/test_humanizer.py
   pytest tests/test_humanizer_russian.py
   ```

2. **Integration tests** – Test full API flows:
   
   ```bash
   pytest tests/test_integration_api.py
   pytest tests/test_integration_db.py
   pytest tests/test_integration_openai.py  # Requires OPENAI_API_KEY
   ```

3. **E2E tests** – Test real resume tailoring with output:
   
   ```bash
   # Requires OPENAI_API_KEY and ResumeEugeneRizov.docx file
   pytest tests/e2e/test_real_resume_tailoring.py::test_russian_job_posting_tailoring -v -s
   ```

4. **API contract tests** – Verify request/response schemas:
   
   ```bash
   pytest tests/test_api_contract.py
   ```

**Test configuration:**

- Tests use SQLite in-memory database by default
- Rate limiting is disabled in tests (see `tests/conftest.py`)
- OpenAI tests are skipped if `OPENAI_API_KEY` is not set

#### Frontend Tests

Frontend E2E tests use Playwright:

```bash
# Install Playwright browsers (first time only)
cd frontend
npx playwright install chromium

# Run E2E tests (requires both servers running)
npx playwright test
```

### Features

- ✅ Resume file upload (DOCX, DOC, PDF) with drag-and-drop
- ✅ Job description input (text or URL fetch)
- ✅ Multi-language support (English, Russian)
- ✅ Multiple target roles (backend, fullstack, GPT engineer)
- ✅ Tailored resume generation with AI humanization
- ✅ Two versions of cover letters (Traditional & Modern)
- ✅ PDF export for resumes and cover letters
- ✅ Keyword coverage analysis
- ✅ Resume history and detail views
- ✅ Diff view (original vs tailored)
- ✅ Error handling with retry and offline detection
- ✅ User authentication (JWT)
- ✅ Rate limiting
- ✅ RAG-based best practices integration

### Development Scripts

**PowerShell scripts:**
- `start.ps1` – Start both backend and frontend
- `stop.ps1` – Stop both services
- `restart.ps1` – Restart both services

**Batch scripts:**
- `start.bat` – Start both backend and frontend
- `stop.bat` – Stop both services
- `restart.bat` – Restart both services

### Dependencies

**Backend:**
- FastAPI
- SQLAlchemy
- OpenAI (optional, for AI features)
- reportlab (for PDF generation)
- python-docx (for DOCX generation)
- beautifulsoup4 (for job URL fetching)

**Frontend:**
- React
- Material-UI
- React Router
- Vite

See `requirements.txt` and `frontend/package.json` for complete lists.

### Deployment

See `DEPLOYMENT.md` for Docker and production deployment instructions.

### License

See `LICENSE` file for details.
