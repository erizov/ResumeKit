FastAPI‑Based Implementation Plan (Current Direction)

1. High‑Level Architecture

- Client (SPA): React + TypeScript + MUI (Vite, single-page app).
- Backend API: Python, FastAPI (REST).
- LLM & AI Layer: OpenAI via `openai` Python SDK (chat completions; embeddings later).
- Storage: SQLite for dev (via SQLAlchemy), PostgreSQL in production via `DATABASE_URL`.
- Cache: optional Redis for rate limiting and caching (later).
- File Storage: local disk for uploads/generated outputs (S3‑compatible later).
- Auth: start as single‑user/no-auth; evolve to simple auth (JWT) using existing `AUTH_*` config.
- Deployment: Docker (backend + frontend) and optional `docker-compose` for API + DB + frontend.

2. Core User Flows

Flow A – First‑time user

- Upload base resume (PDF/DOCX) or paste content.
- Paste job description text.
- Select languages, target roles, and aggressiveness.
- Receive tailored resume variants and notes.

Flow B – Power user (later)

- Reuse stored base resumes and job postings.
- Generate multiple tailored resumes/letters.
- View and filter history of generated outputs.

3. Backend Detailed Plan (FastAPI)

3.1 Main Modules

- `resume_parser` – text extraction from files (implemented).
- `job_parser` – JD normalization and optional URL scraping (later).
- `tailor` – orchestration of stub vs OpenAI-backed tailoring (implemented).
- `llm_client` – OpenAI wrapper using `OPENAI_API_KEY` and `OPENAI_API_BASE` (implemented).
- `db` / `models` – SQLAlchemy setup and entities (implemented).
- `config` – centralized env-based configuration (implemented).

3.2 API Design

MVP (now)

- `POST /api/recommend`
  - Form fields:
    - `job_description` (required).
    - `resume_text` (optional) or `resume_file` (optional PDF/DOCX).
    - `languages` (comma-separated, e.g. `en,ru`).
    - `targets` (comma-separated, e.g. `backend,gpt_engineer`).
    - `aggressiveness` (int 1–3).
  - Behaviour:
    - Use file if provided, otherwise text.
    - Generate one tailored variant per (language × target).
    - Persist `BaseResume`, `JobPosting`, `TailoredResume`.
  - Response:
    - `resumes: List[{id, created_at, language, target, content, notes}]`.

- `GET /api/history`
  - Query params:
    - `limit` (default 20), `offset` (default 0).
    - Optional `language`, `target` filters.
  - Response:
    - `items: List[{id, created_at, language, target}]`.
    - `total: int`.

- `GET /api/tailor/{id}`
  - Path param: `id` of a `TailoredResume`.
  - Response:
    - `{id, created_at, language, target, content, notes, base_resume_text, job_description}`.
- `POST /api/resume/upload` – persist base resume without tailoring (for multi-step flow).
- `POST /api/job/parse-text` – persist JD and return normalized sections.

4. Frontend Detailed Plan (React + MUI)

4.1 Current MVP

- Single-page `App`:
  - Fields for job description, resume text, optional upload, languages, targets, aggressiveness.
  - Calls `POST /api/recommend` via `fetch`.
  - Shows loading, error messages, and result cards for each tailored resume.

4.2 Planned Enhancements

- History view:
  - Table/list backed by `GET /api/history`.
  - Filters for language/target/date.
- Detail view:
  - Uses `GET /api/tailor/{id}`.
  - Shows one tailored resume with metadata and copy/export buttons.
- Optional wizard:
  - Step 1: Upload/save base resume.
  - Step 2: Paste/save JD.
  - Step 3: Configure tailoring options and generate.

5. LLM / OpenAI Integration Strategy

- Models:
  - Default: `gpt-4.1-mini` for tailoring.
  - Optionally `gpt-4.1` for higher quality output later.
- Prompts:
  - System prompt bans fabrication and enforces truthful rewrites.
  - User prompt includes language, target, aggressiveness, JD text, and base resume.
- Controls:
  - Use `RESUMEKIT_USE_OPENAI` flag to toggle between stub and real LLM (keeps tests deterministic).
  - Later add embeddings for keyword coverage and similarity scoring.

6. Data Model (SQLAlchemy)

- `BaseResume`:
  - `id`, `created_at`, `text`.
- `JobPosting`:
  - `id`, `created_at`, `text`.
- `TailoredResume`:
  - `id`, `created_at`, `language`, `target`, `content`, `notes`,
    `base_resume_id`, `job_posting_id`.

Planned additions:

- `user_id` fields when auth is introduced.
- JSON fields for structured resume/JD (PostgreSQL `JSONB`).
- Simple numeric metrics (e.g. coverage score).

7. Non‑Functional Concerns

- Security:
  - Keep secrets in env/.env; never commit real API keys.
  - Avoid logging raw resume/JD text; log only minimal metadata.
- Scalability:
  - Stateless FastAPI app; horizontal scaling behind a reverse proxy.
  - PostgreSQL as primary DB in production.
- Testing:
  - `pytest` unit tests for services (`tailor`, `resume_parser`).
  - FastAPI `TestClient` tests for `/api/recommend` (text + file upload).
  - Later e2e tests for the React frontend.

8. Tech Stack Summary

- Backend:
  - Python, FastAPI, SQLAlchemy, Uvicorn, OpenAI SDK, `python-docx`, `pdfplumber`.
- Frontend:
  - React 18, TypeScript, Vite, MUI.
- Tooling:
  - `pytest`, `.env` + `python-dotenv` (or IDE env), Docker and optional `docker-compose`.


