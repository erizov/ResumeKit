High‑Level Architecture

Client (SPA): React + MUI  
Backend API: Java, Spring Boot (RESTful)  
LLM & AI Layer: OpenAI (Chat Completions + Embeddings) via Spring client  
Storage: PostgreSQL (primary) + Redis (caching)  
File Storage: Local or S3‑compatible (for uploaded resumes / generated PDFs)  
Optional: JasperReports for PDF layout templates  
Auth: Start with simple auth (session/JWT); later OAuth (Google/GitHub) if needed  
Deployment: Dockerized, then to a cloud provider (e.g., Render/Fly.io/Heroku‑like, or k8s)

2. Core User Flows

Flow A – First‑time user

- Upload base resume (PDF/DOCX) or paste content.  
- Paste job URL or JD text.  
- Configure “aggressiveness” of tailoring (conservative ↔ bold).  
- Get:
  - Tailored resume (sections rewritten and reordered)  
  - Highlighted keyword coverage (what’s matched / missing)  
  - Optional tailored cover letter.  
- Download as DOCX/PDF and/or save profile.

Flow B – Power user

- Reuse stored profile (base resume + skills).  
- Paste multiple job postings.  
- Generate multiple tailored resumes/letters.  
- Track which resume was used for which application.

3. Backend Detailed Plan (Spring Boot)

3.1 Main Modules

resume-parser module

- Extract structured data from PDF/DOCX:  
  - Sections: Summary, Experience, Education, Skills, Projects.  
  - For PDF: Apache PDFBox / Tika; for DOCX: Apache POI.  
- Normalize into internal model:  
  - CandidateProfile (name, contact, links)  
  - ExperienceEntry (title, company, timeframe, bullets, tech stack)  
  - SkillSet (hard skills, soft skills)  
- Basic heuristics to detect sections; configurable rules.

job-parser module

- Scrape JD from URL (server‑side HTTP client, fallback to user paste).  
- Use:
  - Spring WebClient or RestClient to fetch HTML  
  - JSoup to strip boilerplate and extract job content.  
- Divide JD into:
  - Role summary, responsibilities, required skills, nice‑to‑have, company info.

nlp-matching module

- Use OpenAI Embeddings or simple keyword extraction:  
  - Normalize skills and technologies (Java, Spring Boot, Kafka, etc.).  
- Compute:
  - Skill overlap between resume and JD  
  - Experience overlap (verbs, responsibilities)  
- Produce:
  - Score per section  
  - List of high‑value missing keywords (to suggest but not fabricate).

resume-tailor (LLM Orchestration)

- Use OpenAI Chat Completion with system prompts:  
  - Rules: no fabrication, prioritize real experiences, preserve chronology.  
- Input: parsed resume JSON + parsed JD JSON + keyword map + user preferences.  
- Tasks:
  - Rewrite summary to match role.  
  - Reorder / slightly rephrase bullets to surface relevant achievements.  
  - Insert missing but true skills already present elsewhere in resume.  
  - Generate optional cover letter.  
- Guardrails:
  - Explicit prompting to avoid inventing roles, companies, titles, dates.  
  - Configuration flags (e.g., “avoid changing job titles”, “don’t change dates”).

template-renderer

- Option 1: Generate HTML + CSS with proper layout and then:  
  - Use Flying Saucer / OpenHTMLtoPDF / wkhtmltopdf to render PDF.  
- Option 2 (optional Jasper):  
  - JasperReports templates (.jrxml) with fields for each resume section.  
  - Convert tailored JSON → JRDataSource → PDF.

persistence module

- Entities:
  - User (auth)  
  - BaseResume (original upload + parsed JSON)  
  - JobPosting (JD text, URL, metadata)  
  - TailoredResume (generated content, download links, timestamps)  
  - TailoredCoverLetter  
- Repositories: Spring Data JPA + PostgreSQL  
- Redis:
  - Cache JD parsing result by URL hash.  
  - Cache embeddings or partial LLM results (optional, for cost).

metrics & logging

- Actuator endpoints (health, metrics).  
- Custom metrics:
  - Tailoring requests count  
  - Average LLM latency  
  - Token usage by user (if multi‑tenant).  
- Structured logging with Slf4j, JSON logs optional.

3.2 API Design (REST)

Auth

- POST /api/auth/signup  
- POST /api/auth/login  
- POST /api/auth/logout

Resume

- POST /api/resume/upload (multipart) → store + parse → CandidateProfile.  
- GET /api/resume/base → current user base resume (structured + raw).

Job Posting

- POST /api/job/fetch (JSON: { url }) → parsed JD.  
- POST /api/job/parse-text (JD text) → parsed JD.

Tailoring

- POST /api/tailor  
  - Body: resumeId, jobId|jobText, preferences.  
  - Response: tailored resume data (sections + HTML) + coverage metrics.  
- GET /api/tailor/{id} → retrieve past tailored version.

Export

- GET /api/tailor/{id}/pdf  
- GET /api/tailor/{id}/docx (optional, docx4j).

Analytics (later)

- GET /api/reports/usage (simple stats per user).

4. Frontend Detailed Plan (React + MUI)

4.1 Structure

Tech

- React (Vite or CRA), TypeScript  
- React Query / TanStack Query for API calls & caching  
- React Router  
- MUI (core + icons)  
- Form library (React Hook Form)

Top‑Level Pages

- AuthPage: login/signup  
- DashboardPage: overview of resumes and JDs  
- UploadResumePage:
  - Drag‑and‑drop upload, preview parsed structure.  
- JobInputPage:
  - Input URL or paste text, show parsed job structure.  
- TailorPage:
  - Side‑by‑side:
    - Left: job description + keyword highlights.  
    - Center: tailored resume editor (sections).  
    - Right: coverage stats & suggestions.  
- HistoryPage: list of generated resumes & letters.

4.2 Key UI Features

Resume editor

- Section‑based, collapsible cards (Summary, Experience, Skills).  
- Editable fields but clearly show LLM‑generated changes (e.g. color coding).

Keyword coverage visualization

- MUI Chips for required skills:
  - Green = present in tailored resume  
  - Yellow = possible (inferred)  
  - Red = missing

Diff display

- Show basic “before vs after” diff for each section (e.g., collapse/expand).

Export

- Buttons for “Download PDF” / “Copy to Clipboard / DOCX”.

5. LLM / OpenAI Integration Strategy

Model choice

- GPT‑4.1 (or 4.1‑mini for cheaper iterations).

Endpoints

- Chat completions for rewriting + cover letter.  
- Embeddings for similarity (optional but recommended).

Prompt design

- System prompt defines:
  - No fabrication policy  
  - Target style: concise, metric‑driven bullets, strong verbs.  
  - Region/language preferences if needed.  
- User prompt includes:
  - Parsed resume JSON  
  - Parsed JD JSON  
  - Computed keyword overlap + list of missing keywords  
  - Instructions on aggressiveness level.

Cost & Rate‑Limiting

- Store token usage per user.  
- Simple rate limiter using Redis (e.g., X requests/hour).

6. Data Model (Conceptual)

User

- id, email, passwordHash (or OAuth sub), settings.

BaseResume

- id, userId, rawFilePath, parsedJson (JSONB), createdAt, updatedAt.

JobPosting

- id, userId, url, rawText, parsedJson (JSONB), createdAt.

TailoredResume

- id, userId, baseResumeId, jobPostingId,  
  tailoredJson (JSONB), html, pdfPath?, score, createdAt.

TailoredCoverLetter

- id, tailoredResumeId, text, html, pdfPath?.

7. Non‑Functional Concerns

Security

- HTTPS only.  
- Store API keys via environment variables / secrets manager.  
- Content filtering to avoid leaking sensitive data (e.g., mask phone/email in logs).

Scalability

- Stateless Spring Boot app with LLM as external dependency.  
- Horizontal scaling via containers.

Testing

- Unit tests for parsing & matching logic (Java + JUnit 5).  
- Component/integration tests for key endpoints.  
- Frontend tests for main flows (React Testing Library / Cypress).

8. Suggested Tech Stack (Summary)

Backend

- Language: Java 17+  
- Framework: Spring Boot 3.x (Web, Data JPA, Security, Actuator)  
- HTTP Client: Spring WebClient or RestClient  
- Parsing:
  - Apache Tika / PDFBox, Apache POI  
  - JSoup for JD HTML parsing  
- DB: PostgreSQL  
- Cache/Rate limiting: Redis  
- LLM: OpenAI Java client or custom WebClient against OpenAI REST  
- PDF: OpenHTMLtoPDF or JasperReports (optional)  
- Build: Maven or Gradle (your preference)

Frontend

- React + TypeScript  
- Vite (or CRA) as bundler  
- Material UI  
- React Query, React Router, React Hook Form

DevOps

- Docker for backend and frontend  
- docker-compose for local dev (app + Postgres + Redis)  
- CI (GitHub Actions / GitLab CI): run tests, lint, build images


