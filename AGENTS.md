# JP Game Localizer MVP — Agent Guide

## Project Overview

This repository is a two-package monorepo:

```text
jp-game-localizer-mvp/
├── backend/   # FastAPI, SQLAlchemy, SQLite, Python
└── frontend/  # Next.js, React, TypeScript, Tailwind CSS
```

The project is a resource-efficient Japanese-to-English game localization MVP.

It supports:

* Structured game-context upload
* Multi-format Japanese script upload
* Scene-based chunking
* Context-aware LLM localization
* Rolling memory between scenes
* Human review and editing
* CSV and JSON export

The current system uses prompt-based domain adaptation. It is not a trained or fine-tuned game-domain translation model.

---

## Repository Rules

Before changing code:

1. Inspect the relevant files and existing implementation.
2. Preserve the current working workflow.
3. Change only files required for the current task.
4. Implement one revision phase at a time.
5. Do not refactor unrelated code.
6. Run relevant validation commands after every change.
7. Report:

   * files changed,
   * behavior changed,
   * tests executed,
   * build results,
   * known limitations.

Do not claim professional localization quality unless supported by evaluation evidence.

AI-generated translations must remain drafts until human review.

Do not print or expose complete uploaded scripts in logs.

Keep the LLM client provider-neutral. Do not replace the OpenAI-compatible abstraction with Groq-specific application logic.

---

## Backend

### Stack

* Python
* FastAPI
* SQLAlchemy
* SQLite
* Pydantic
* Uvicorn
* OpenAI-compatible LLM client

### Setup

```bash
cd backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

### Environment Variables

The local backend configuration is stored in:

```text
backend/.env
```

Expected variables:

```env
DATABASE_URL=sqlite:///./localizer.db
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=
```

Never commit `backend/.env`.

### Backend Architecture Notes

* Database tables are currently created at startup using `Base.metadata.create_all()`.
* Alembic migrations are not currently configured.
* `backend/app/services/localization_service.py` is an unused stub.
* The active translation flow is implemented in `backend/app/routes/translate.py`.
* The LLM client is implemented in `backend/app/ai/llm_client.py`.
* The LLM client retries without JSON response mode when a provider rejects structured output or returns a token-related failure.
* Rolling-memory validation and fallback behavior are implemented in `backend/app/services/memory_service.py`.
* Demo files are available in:

  * `backend/demo/context.yaml`
  * `backend/demo/script.csv`
  * `backend/demo/run_demo.md`

---

## Frontend

### Stack

* Next.js
* React
* TypeScript
* Tailwind CSS

### Setup

```bash
cd frontend

npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

### Validation

```bash
npm run lint
npm run build
```

There is currently no dedicated `npm run typecheck` script. Until one is added, use the production build to catch TypeScript compilation errors.

### Frontend Environment

The frontend configuration is stored in:

```text
frontend/.env.local
```

Expected variable:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Never commit `frontend/.env.local`.

### Next.js Guidance

Before changing frontend behavior:

* Inspect the installed Next.js version and existing project conventions.
* Do not assume examples from older Next.js versions apply.
* Preserve the current App Router structure.
* Keep frontend API response interfaces aligned with actual FastAPI responses.

---

## Current Known Gaps

* No automated backend tests
* No automated frontend tests
* No CI workflow
* No Alembic database migrations
* No authentication or authorization
* No project deletion endpoint
* No background translation queue
* No batch translation workflow
* No translation memory
* No formal game-domain benchmark
* No automated localization-quality scoring
* No deterministic glossary enforcement
* Limited export formats

These are known MVP limitations, not hidden production features.

---

## Security and Privacy Rules

Never commit:

```text
.env
.env.local
backend/.env
frontend/.env.local
localizer.db
*.db
venv/
backend/venv/
node_modules/
frontend/node_modules/
.next/
frontend/.next/
__pycache__/
*.pyc
```

Additional rules:

* Do not log API keys.
* Do not log entire uploaded scripts.
* Do not expose confidential project content in exception messages.
* Do not call live external LLM APIs in automated tests.
* Use mocked LLM responses in tests.
* Treat uploaded scripts and context as potentially confidential.
* Production privacy requires authentication, authorization, encryption, retention controls, deletion workflows, audit logging, and suitable AI-provider agreements or private deployment.

---

## Core API Workflow

```text
Upload context
→ Upload script
→ Create scene chunks
→ Translate chunk
→ Generate and propagate rolling memory
→ Review and edit translations
→ Export CSV or JSON
```

Important endpoints include:

```text
POST /upload/context
POST /upload/script/{project_id}
POST /chunks/create/{project_id}
GET  /chunks/{project_id}
GET  /chunks/detail/{chunk_id}
POST /translate/chunk/{chunk_id}
GET  /translate/{chunk_id}
PATCH /translate/{translation_id}
GET  /export/{project_id}?format=csv
GET  /export/{project_id}?format=json
```

---

## Revision Workflow

All major improvements should follow:

```text
Inspect
→ Plan
→ Approve
→ Implement
→ Test
→ Review diff
→ Commit
```

Implement only one revision phase at a time.

For each phase:

* Preserve backward compatibility where practical.
* Avoid duplicating translation logic.
* Add tests using mocks or fixtures.
* Do not call paid or external LLM APIs during automated validation.
* Run backend checks.
* Run frontend lint/build checks when frontend files are changed.
* Review `git diff` before committing.

---

## Git Rules

Before starting work:

```bash
git status
git log --oneline -5
```

After implementation:

```bash
git diff
git status
```

Do not commit:

* secrets,
* databases,
* virtual environments,
* generated frontend builds,
* dependency folders,
* temporary uploads,
* exported user files.

Use descriptive commits focused on one phase or fix.

---

## Testing Gotchas

* `SourceFile` column is `original_filename`, not `filename`. Writing `filename=` will fail silently via SQLAlchemy (accepted but ignored by the constructor — the column won't be set).
* Translation objects must be explicitly `db_session.add(txn)`-ed before `commit()`. Instantiating `Translation(...)` without adding it will create no row and produce no error. Export queries use `outerjoin(Translation)` — a missing translation produces `status="pending"` with empty localized text.
* When a helper method in a test class needs to be called from a different test class, annotate it with `@staticmethod` so it can be called as `TestClass.method(db_session)` without instantiation.
