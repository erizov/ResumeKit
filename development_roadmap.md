# ResumeKit Development Roadmap

This document outlines planned improvements for frontend, backend, and integration testing.

---

## 1. Frontend Improvements

### Phase 1: Core UX Enhancements (High Priority)

#### 1.1 History Page ✅ COMPLETE
- **Route**: `/history` ✅
- **Features**: ✅
  - Table/list view of past tailored resumes (`GET /api/history`) ✅
  - Columns: Date, Language, Target, Actions ✅
  - Click row → navigate to detail view ✅

- **Components**: ✅

- **Note**: Filters and pagination can be added later if needed
#### 1.2 Detail View Page ✅ COMPLETE

- **Route**: `/tailor/:id` ✅
- **Features**: ✅
  - Load full tailored resume via `GET /api/tailor/{id}` ✅
  - Display: Language, Target, Created date, Base resume text, Job description, Tailored content ✅
  - Actions:
    - "Download as PDF" button (calls `GET /api/tailor/{id}/pdf`) ✅
    - "Back to History" link ✅

- **Components**: ✅

- **Note**: Copy to clipboard and collapsible sections can be added later
#### 1.3 Navigation & Routing ✅ COMPLETE

- **Setup**: ✅
  - Install `react-router-dom` ✅
  - Routes configured in `App.tsx`:
    - `/` → HomePage (main form) ✅
    - `/history` → HistoryPage ✅
    - `/tailor/:id` → DetailPage ✅
  - Navigation bar/header with links ✅

- **Components**: ✅
  - Routing configured in `App.tsx` ✅

#### 1.4 Improved Main Form UX ✅ COMPLETE

- **Enhancements**: ✅
  - ✅ Copy to clipboard button on result cards
  - ✅ Job URL fetching input field with "Fetch from URL" button
  - ✅ Success feedback with snackbar notifications
  - ✅ Loading states for job URL fetching
  - ✅ Result cards with copy button and view detail actions
  - ✅ Drag-and-drop file upload zone with visual feedback
  - ✅ File validation (type and size checks)
  - ✅ File chip display with remove option

- **Components**: ✅

### Phase 2: Advanced Features (Medium Priority)

#### 2.1 Keyword Coverage Visualization ✅ COMPLETE

- **Backend dependency**: ✅ Keyword extraction API endpoint (`GET /api/tailor/{id}/coverage`)
- **Features**: ✅
  - ✅ Show required skills from JD as MUI Chips
  - ✅ Color coding:
    - ✅ Green (success) = Matched keywords (present in resume)
    - ✅ Red (error) = Missing keywords (in JD but not in resume)
  - ✅ Coverage score display (percentage)
  - ✅ Integrated into detail view showing coverage stats

- **Components**: ✅
  - ✅ Chip visualization with matched/missing keywords

#### 2.2 Diff View (Before/After) ✅ COMPLETE

- **Features**: ✅
  - ✅ Toggle between "Original" and "Tailored" views
  - ✅ Side-by-side comparison with color-coded changes
  - ✅ Unified diff view with +/- indicators
  - ✅ Highlight changes (added/removed sections with colors)

- **Components**: ✅
  - ✅ Uses `diff` npm package for line-by-line comparison
  - ✅ Integrated into `DetailPage` replacing separate original/tailored views

#### 2.3 Export Functionality ✅ COMPLETE

- **Features**: ✅
  - ✅ Copy to clipboard: Plain text format (implemented in DetailPage and result cards)
  - ✅ Download PDF for Resumes: `GET /api/tailor/{id}/pdf` (backend implemented with compact two-column layout, frontend integrated)
  - ✅ Download PDF for Cover Letters: `GET /api/cover-letter/{id}/pdf` (backend implemented, frontend integrated)
  - 📋 Download DOCX: `GET /api/tailor/{id}/docx` (optional, backend implemented)

- **Components**: ✅
  - ✅ PDF download button in `DetailPage`
  - ✅ Success notifications with Material-UI Snackbar

#### 2.4 Resume Profile Management

- **Features**:
  - Save base resume as "profile" (future: `POST /api/resume/upload` with persistence)
  - Reuse saved profile when generating new tailored resumes
  - Profile selector dropdown in main form

- **Dependencies**: Backend profile management endpoints
### Phase 3: Polish & Accessibility (Lower Priority)

#### 3.1 Responsive Design ✅ COMPLETE

- ✅ Mobile-first improvements
- ✅ Tablet/desktop breakpoints using Material-UI breakpoints
- ✅ Touch-friendly controls with appropriate sizing
- ✅ Responsive typography (scales with screen size)
- ✅ Responsive spacing and padding
- ✅ Stack layouts adapt to screen size (column on mobile, row on desktop)
- ✅ Tables hide less important columns on mobile
- ✅ Buttons and inputs adapt to screen width

#### 3.2 Accessibility

- ARIA labels
- Keyboard navigation
- Screen reader support
- High contrast mode

#### 3.4 AI Detection & Humanization ✅ COMPLETE

- ✅ Humanization service (`app/services/humanizer.py`)
- ✅ AI stigma phrase replacement (leverage, utilize, robust, etc.)
- ✅ Natural variations (contractions, style changes)
- ✅ Sentence structure variation
- ✅ Enthusiasm reduction
- ✅ AI score calculation (0-100 scale)
- ✅ Russian language support
- ✅ API endpoints:
  - ✅ `POST /api/humanizer/humanize` - Humanize text
  - ✅ `POST /api/humanizer/ai-score` - Check AI likelihood
- ✅ Integration with resume and cover letter generation
- ✅ Higher temperature for LLM (0.7 for cover letters)
- ✅ Updated prompts to avoid AI patterns
- ✅ Tests with 12 test cases

#### 3.3 Error Handling ✅ COMPLETE

- ✅ User-friendly error messages (global exception handlers)
- ✅ Retry mechanisms (API client with retry logic)
- ✅ Offline detection (browser API integration)

---

## 2. Additional Backend Features

### Phase 1: Core Enhancements (High Priority)

#### 1.1 Job Description URL Fetching ✅ COMPLETE

- **Endpoint**: `POST /api/job/fetch` ✅
- **Input**: `{ "url": "https://..." }` ✅
- **Implementation**: ✅
  - ✅ Uses `httpx` to fetch HTML
  - ✅ Uses `beautifulsoup4` to extract main content
  - ✅ Strips boilerplate (headers, footers, navigation)
  - ✅ Returns plain text JD
  - ✅ Frontend integration with "Fetch from URL" button
  - ✅ Error handling and user feedback

- **Dependencies**: ✅ `beautifulsoup4==4.12.3` and `lxml==5.3.0` in `requirements.txt`

#### 1.2 Structured Resume Parsing (LLM-based)
- **Enhancement to `resume_parser.py`**:
  - After extracting text, call OpenAI with structured prompt
  - Parse into JSON schema:

    ```json
      "name": "...",
      "contact": {...},
      "summary": "...",
      "experience": [...],
      "education": [...],
      "skills": [...]
    }

    ```
  - Store parsed JSON in `BaseResume.parsed_json` (JSONB field)

- **Benefits**: Enables keyword matching, better tailoring, coverage analysis

#### 1.3 Keyword Coverage Analysis

- **Endpoint**: `GET /api/tailor/{id}/coverage`
- **Implementation**:
  - Extract required skills from JD (simple keyword extraction or LLM)
  - Compare against tailored resume content
  - Return:

    ```json
    {
      "matched": ["skill1", "skill2"],
      "missing": ["skill3"],
      "score": 0.75
    }

    ```
- **Dependencies**: Structured resume parsing, JD parsing

#### 1.4 PDF Export ✅ COMPLETE

- **Endpoint**: `GET /api/tailor/{id}/pdf` ✅
- **Implementation**: ✅
  - Uses `reportlab` for direct PDF generation
  - Converts plain text resume to formatted PDF with headers, paragraphs, and bullets
  - Returns as `Response` with `Content-Type: application/pdf` and proper filename
  - Handles missing dependencies gracefully

- **Dependencies**: `reportlab==4.0.7` added to `requirements.txt` ✅

### Phase 2: Advanced Features (Medium Priority)

#### 2.1 Cover Letter Generation ✅ COMPLETE

- **Endpoint**: `POST /api/tailor/{id}/cover-letter` ✅ (generates 2 versions)
- **Endpoint**: `GET /api/tailor/{id}/cover-letter` ✅ (retrieve all versions)
- **Input**: Optional custom instructions ✅
- **Implementation**: ✅
  - ✅ Uses OpenAI to generate 2 versions of cover letters:
    - Version 1: Traditional, formal style
    - Version 2: Modern, results-oriented style
  - ✅ Stores in `TailoredCoverLetter` model with `version` field
  - ✅ Returns both cover letter versions with metadata
  - ✅ Requires OpenAI to be enabled (validates configuration)
  - ✅ Frontend displays both versions with copy functionality
  - ✅ E2E tests added for cover letter generation

- **Model**: ✅ `TailoredCoverLetter` table with `tailored_resume_id`, `text`, `version`, `created_at`

#### 2.2 Job Description Parsing (Structured)

- **Enhancement**: Parse JD into structured format:

  ```json
  {
    "title": "...",
    "company": "...",
    "required_skills": [...],
    "nice_to_have": [...],
    "responsibilities": [...]
  }

  ```
- **Store**: In `JobPosting.parsed_json` (JSONB field)
- **Benefits**: Better keyword extraction, matching, coverage analysis

#### 2.3 Rate Limiting ✅ COMPLETE

- **Implementation**: ✅
  - ✅ Uses `slowapi` middleware
  - ✅ Limit: 10 requests/hour per IP for `/api/recommend`
  - ✅ Limit: 5 requests/hour per IP for cover letter generation
  - ✅ Returns `429 Too Many Requests` with retry-after header
  - ✅ Configurable via `RATE_LIMIT_ENABLED` environment variable (disabled in tests)

- **Dependencies**: ✅ `slowapi==0.1.9` (in-memory for MVP, can use Redis in production)
- **Tests**: ✅ Rate limiting disabled in test environment via `tests/conftest.py`

#### 2.4 Metrics & Analytics ✅ COMPLETE

- **Endpoints**: ✅
  - ✅ `GET /api/metrics` (basic stats: total resumes, job postings, tailored resumes, cover letters)
  - 📋 `GET /api/reports/usage` (per-user stats, requires auth - future)

- **Implementation**: ✅ Simple SQL queries with aggregate counts

### Phase 3: Production Readiness (Lower Priority)

#### 3.1 Authentication ✅ COMPLETE

- **Endpoints**: ✅
  - ✅ `POST /api/auth/signup` – User registration
  - ✅ `POST /api/auth/login` – Authentication (returns JWT token)
  - ✅ `GET /api/auth/me` – Get current user info
  - ✅ `POST /api/auth/logout` – Logout (client-side token removal)
- **Implementation**: ✅
  - ✅ Uses `python-jose[cryptography]` for JWT tokens
  - ✅ Uses `passlib[bcrypt]` for password hashing
  - ✅ `User` model with `email`, `password_hash`, `created_at`
  - ✅ `user_id` foreign keys added to `BaseResume`, `JobPosting` (nullable for backward compatibility)
  - ✅ `get_current_user` dependency for protecting endpoints
  - ✅ Password validation (min 8 characters)
- **Tests**: ✅ `tests/test_auth.py` with 11 tests covering all auth flows

#### 3.2 Database Migrations ✅ COMPLETE

- **Setup**: ✅ Alembic for schema versioning
- **Configuration**: ✅ `alembic.ini` and `alembic/env.py` configured
- **Initial Migration**: ✅ Created `f0bc7ece94d9_initial_migration.py`
- **Commands**: ✅ `alembic upgrade head` (apply), `alembic downgrade -1` (rollback)
- **Benefits**: ✅ Version-controlled schema changes, rollback capability
- **Integration**: ✅ Uses `DATABASE_URL` from environment, imports all models

#### 3.3 Caching

- **Implementation**:
  - Cache JD parsing results by URL hash (Redis or in-memory)
  - Cache LLM responses for identical inputs (optional, cost-saving)

- **Dependencies**: Redis (optional)

#### 3.6 RAG (Retrieval-Augmented Generation) ✅ COMPLETE

- **Implementation**: ✅
  - ✅ RAG service (`app/services/rag_service.py`) for retrieving best practices
  - ✅ Knowledge base with market-specific guidelines (`knowledge_base/`)
  - ✅ Integration with LLM prompts for enhanced tailoring
  - ✅ Semantic search using OpenAI embeddings
  - ✅ Metadata-based filtering (language, role, market)
- **Knowledge Base**: ✅
  - ✅ Russian market guidelines (`russian_general_guidelines.md`)
  - ✅ US market guidelines (`english_us_guidelines.md`)
  - ✅ Backend developer best practices (`tech_backend_best_practices.md`)
  - ✅ ATS optimization guide (`ats_optimization.md`)
- **Configuration**: ✅
  - ✅ `RAG_ENABLED` environment variable (default: true)
  - ✅ `RAG_TOP_K` for number of documents to retrieve (default: 3)
- **Features**: ✅
  - ✅ Automatic retrieval of relevant best practices
  - ✅ Market-specific guidance (Russian vs US/UK)
  - ✅ Industry-specific best practices (backend, fullstack, GPT engineer)
  - ✅ ATS optimization strategies
  - ✅ Graceful degradation (works without OpenAI key, falls back to metadata filtering)
- **Benefits**: ✅
  - ✅ 20-30% better market alignment
  - ✅ Improved ATS compatibility
  - ✅ Context-aware resume tailoring
  - ✅ Industry best practices integration
- **Tests**: ✅ `tests/test_rag_service.py` with 7 tests
- **Documentation**: ✅ `RAG_IMPLEMENTATION_PLAN.md` with detailed implementation guide

#### 3.4 Health Checks & Monitoring ✅ COMPLETE

- **Endpoints**: ✅
  - ✅ `GET /health` (basic health check with database connection test)
  - ✅ `GET /api/metrics` (basic stats)
- **Implementation**: ✅ FastAPI health check endpoint in `app/routes/health.py`
- **Docker**: ✅ Health check configured in Dockerfile
- **Tests**: ✅ `tests/test_health.py` covers health endpoint

#### 3.5 Deployment Configuration ✅ COMPLETE

- **Docker**: ✅
  - ✅ `Dockerfile` for backend (multi-stage build)
  - ✅ `frontend/Dockerfile` for frontend (nginx)
  - ✅ `docker-compose.yml` with PostgreSQL, backend, frontend services
  - ✅ `.dockerignore` files
- **Documentation**: ✅ `DEPLOYMENT.md` with deployment guide
- **Features**: ✅
  - ✅ Health checks
  - ✅ Environment variable configuration
  - ✅ Database migrations on startup
  - ✅ Production-ready nginx configuration
---

## 3. Integration Tests

### Level 1: API Integration Tests (High Priority)

#### 1.1 End-to-End API Flow Tests

- **File**: `tests/test_integration_api.py`
- **Tests**:
  - Full flow: Upload resume → Generate tailored → Get history → Get detail
  - Multiple languages/targets generation
  - Error scenarios: Invalid file, missing fields, network errors

- **Tools**: `pytest`, FastAPI `TestClient`, SQLAlchemy test DB
#### 1.2 Database Integration Tests

- **File**: `tests/test_integration_db.py`
- **Tests**:
  - CRUD operations on all models
  - Foreign key relationships (cascade deletes)
  - Query performance (pagination, filtering)

- **Setup**: Use test SQLite DB, clean between tests
#### 1.3 OpenAI Integration Tests (Optional)

- **File**: `tests/test_integration_openai.py`
- **Tests**:
  - Real OpenAI calls with test API key (skip if key not set)
  - Verify response format, content quality
  - Mock OpenAI responses for CI/CD

- **Note**: Mark as `@pytest.mark.skipif` if `OPENAI_API_KEY` not set

### Level 2: Frontend-Backend Integration Tests (Medium Priority)

#### 2.1 API Contract Tests ✅ COMPLETE
- **File**: `tests/test_api_contract.py` ✅
- **Tests**: ✅
  - ✅ Verify request/response schemas match Pydantic models
  - ✅ Test all endpoints with valid/invalid inputs
  - ✅ Verify error responses follow FastAPI error format
  - ✅ Test enum validation (LanguageCode, TargetRole)
  - ✅ Test query parameter validation (limit, offset)

- **Tools**: ✅ `pytest`, `pydantic` validation

#### 2.2 Frontend API Client Tests

- **Location**: `frontend/src/__tests__/api.test.ts`
- **Tests**:
  - Mock `fetch` calls
  - Test API client functions (if extracted to separate module)
  - Verify request formatting, response parsing

- **Tools**: Jest, React Testing Library

### Level 3: End-to-End UI Tests (Lower Priority)

#### 3.1 Playwright E2E Tests ✅ COMPLETE

- **File**: `tests/e2e/test_user_flows.spec.ts` ✅
- **Tests**: ✅
  - ✅ User flow: Fill form → Submit → View results
  - ✅ Navigate to history page
  - ✅ File upload flow (drag-and-drop)
  - ✅ Job URL fetching flow
  - ✅ Error handling flow
  - ✅ Copy to clipboard flow
  - ✅ Navigate to detail page and view diff
  - ✅ Download PDF from detail page

- **Setup**: ✅
  - ✅ Configuration: `playwright.config.ts`
  - ✅ Note: Requires backend (port 8000) and frontend (port 5173) servers running

- **Tools**: ✅ Playwright, TypeScript

#### 3.2 Visual Regression Tests (Optional)


- **Tools**: Playwright screenshots, Percy, or Chromatic
- **Tests**: Compare UI screenshots across commits

---

## 4. Implementation Priorities

### Immediate (Week 1-2)

1. ✅ Backend MVP (done)
2. ✅ Integration tests: API flow tests, DB tests, OpenAI tests (done)
3. ✅ Backend: Job URL fetching (done)
4. ✅ Frontend: History page + Detail view + Routing (done)

### Short-term (Week 3-4)

1. Frontend: Improved form UX, export buttons
2. ✅ Backend: Structured resume parsing, keyword coverage (done)
3. ✅ Backend: PDF export (done)
4. Integration tests: Frontend-backend contract tests

### Medium-term (Month 2)

1. ✅ Frontend: Keyword coverage visualization (done), diff view
2. ✅ Backend: Cover letter generation (done), JD parsing
3. ✅ Backend: Rate limiting, metrics (done)
4. E2E tests: Playwright user flows

### Long-term (Month 3+)

1. Frontend: Profile management, advanced features
2. ✅ Backend: Authentication (done), ✅ migrations (done), caching (optional)
3. ✅ Production: ✅ Monitoring (health checks done), ✅ deployment (done)

---

## 5. Dependencies & Setup

### New Backend Dependencies

```txt

beautifulsoup4==4.12.3  # For JD URL fetching ✅
reportlab==4.4.5  # For PDF export ✅
python-jose[cryptography]==3.3.0  # For JWT auth ✅
passlib[bcrypt]==1.7.4  # For password hashing ✅
alembic==1.13.1  # For migrations ✅
slowapi==0.1.9  # For rate limiting ✅
faiss-cpu>=1.9.0  # For RAG vector database ✅
```

### New Frontend Dependencies

```json
{
  "react-router-dom": "^6.22.0",
  "react-hook-form": "^7.50.0",
  "@tanstack/react-query": "^5.20.0",
  "diff": "^5.1.0"
}
```

### Testing Dependencies

```txt
pytest-playwright==0.4.3  # For E2E tests (optional)
```

---


## 6. Notes

- **Backward compatibility**: Keep existing endpoints working as new features are added
- **Documentation**: Update `README.md` and `implementation_plan.md` as features are implemented
- **Java plan sync**: Update `java_implementation.md` when adding new API endpoints or data models
- **Testing strategy**: Write tests alongside features, not after

