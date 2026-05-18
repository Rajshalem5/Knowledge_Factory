<!--
  Sync Impact Report:
  - Version change: 0.0.0 → 1.0.0 (initial ratification)
  - All 7 principles defined from scratch
  - Sections added: Tech Stack, Security & Compliance, Development Workflow, Pipeline Conventions, Governance
  - Templates all pending first use (no prior templates existed)
  - No deferred placeholders
-->

# Knowledge Factory Constitution

## Core Principles

### I. Spec-Driven, Not Vibe-Driven

Every feature begins with a specification written via `/speckit-specify` before any code is written. The spec defines **what** and **why**, not **how**. The technical plan (`/speckit-plan`) and task list (`/speckit-tasks`) are derived from the spec, reviewed, and only then implemented (`/speckit-implement`). No feature shall be implemented without a corresponding spec, with the sole exception of hotfixes for production-blocking bugs (see V.Hotfixes).

### II. Pipeline-Aware Architecture

Knowledge Factory is a **candidate screening and assessment pipeline**. Every change MUST consider which pipeline stage it affects:

- PRE-APPLICATION (landing, registration, eligibility config)
- SCREENING (eligibility evaluation, ROUND1_PASSED/REJECTED)
- ASSESSMENT (ROUND2 and ROUND3, code execution, AI evaluation)
- INTERVIEW (scheduling, feedback)
- SELECTION (final decision)

No change shall break the forward progression of candidates through these stages. Additive changes to status values require updates to the enum, DB migration, and the pipeline-stats endpoint.

### III. Database Schema Hygiene

The SQLite development database (`knowledge_factory.db`) MUST remain in sync with ORM model definitions. Before any commit that touches a model file, run:

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('knowledge_factory.db')
for row in conn.execute('SELECT name FROM sqlite_master WHERE type=\\'table\\''):
    cols = conn.execute(f'PRAGMA table_info({row[0]})').fetchall()
    print(f'{row[0]}: {sorted(c[1] for c in cols)}')
"
```

Compare output against model columns. Missing columns MUST be added via `ALTER TABLE` before the change is considered complete. The following pitfalls are non-negotiable:

- NEVER use `lazy="selectin"` on `Candidate` relationships — it cascades schema mismatches to login crashes. Use `lazy="select"` (deferred) instead.
- NEVER use `UUID(as_uuid=False)` from `sqlalchemy.dialects.postgresql` — it strips dashes on SQLite. Use `PortableUUID` from `app.database`.
- NEVER pass `statement_cache_size` in `connect_args` to `create_async_engine()` — it is asyncpg-only and crashes aiosqlite.
- ALWAYS run `PRAGMA table_info(table)` to verify column existence after model changes.
- ALWAYS verify `back_populates` relationships are defined on BOTH sides of the relationship.

### IV. AI Question Generation Rules

AI-generated assessment questions MUST adhere to these constraints:

- `seed` parameter is NOT supported by AWS Bedrock via litellm — never include it in the request payload.
- Temperature MUST be set high enough (>= 0.7) to ensure uniqueness when generating multiple questions in a batch.
- The AI endpoint runs through litellm → AWS Bedrock. Test the API connection independently before wiring through the app (see `.env` verification protocol in the pipeline skill references).
- Question deduplication MUST happen at the application layer (not the AI layer) — compare question text hashes, not IDs.

### V. Code Execution Sandbox Safety

The Piston sandbox (code execution engine) has these invariants:

- Language names follow Piston conventions, not standard ones: `python` not `python3`, `javascript` not `node`.
- The sandbox URL (via ngrok) requires the header `ngrok-skip-browser-warning: true` on every request.
- Before any feature that depends on code execution, verify the sandbox is running: `curl -s $SANDBOX_URL/runtimes | head -1`.
- The sandbox is an external service — NEVER expose it directly to candidates. Always proxy through `POST /api/code/execute` which adds auth, rate limiting, and Piston-agnostic language mapping.

### VI. Frontend Integration Constraints

- `VITE_API_URL` is baked into the JS bundle at build time. If it points to `http://localhost:8000`, loading the SPA from a different origin (ngrok, production domain) causes CORS/mixed-content failures. For production, set `VITE_API_URL=""` (relative paths) and rebuild.
- JWT access tokens are stored in-memory only (module closure). Page refresh triggers cookie-based refresh via `POST /api/auth/refresh` which reads the httpOnly `kf_refresh_token` cookie. If the refresh flow breaks, users are logged out on page reload.
- Never use `browser_click` for React form submissions in automated testing — React's synthetic events may not fire. Use `browser_console` with `document.querySelector(...).click()` instead.
- TanStack Query is used for data fetching. Endpoint changes that affect response shapes MUST be accompanied by frontend query key invalidation updates.

### VII. Security & Compliance (Non-Negotiable)

These rules from `AGENTS.md` are incorporated by reference and apply to all code:

**Secrets:** Never hardcode credentials. Never put secrets in VITE_/NEXT_PUBLIC_/REACT_APP_ env vars. `.env` MUST be in `.gitignore` before first commit.

**Auth:** Every protected endpoint MUST authenticate via `Depends(require_role([...]))` or `Depends(get_current_user)` before the handler body. Resource ownership MUST be verified separately from authentication (`current_user.id == resource.owner_id`).

**Input:** Never concatenate user input into SQL — always use ORM parameters. File uploads validate type by magic bytes, not extension. All user input validated server-side.

**Output:** Never expose stack traces, SQL errors, or file paths in API responses. Production errors return `{"detail": "Internal Server Error"}`.

**Rate Limiting:** Login and registration endpoints MUST be rate-limited (N failed attempts per IP within a time window). Do not trust `X-Forwarded-For` without a trusted reverse proxy.

## Technology Stack & Architecture

### Backend
- **Framework:** FastAPI with async SQLAlchemy 2.0 (aiosqlite for dev, asyncpg for production PostgreSQL)
- **Auth:** JWT access token (in-memory) + httpOnly refresh token cookie (7-day expiry, path=`/api/auth`)
- **AI:** litellm → AWS Bedrock for question generation and evaluation
- **Code Execution:** Piston sandbox (external Docker container, proxied via ngrok)
- **Migrations:** Alembic (single migration currently — `4e7e100fb216_initial_clean_schema`)

### Frontend
- **Framework:** React + Vite + TypeScript
- **State Management:** TanStack Query (server state), in-memory JWT store
- **Styling:** CSS modules / Tailwind

### Pipeline Stages
```
APPLIED → ROUND1_PASSED → ROUND2_IN_PROGRESS → ROUND2_PASSED
  → ROUND3_IN_PROGRESS → ROUND3_PASSED → INTERVIEW_SCHEDULED
  → INTERVIEW_COMPLETED → SELECTED
(Reject path at ROUND1/2/3: _REJECTED)
```

## Development Workflow

### Branch & Commit
- Default branch: `dev`. Feature branches: `feature/<short-description>`.
- Commit convention: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- Each commit is a single logical change. One change per commit, granular not monolithic.
- No git history rewrite. Never force push without explicit user approval.

### Feature Lifecycle
1. `/speckit-specify` — define scope and user stories
2. `/speckit-plan` — technical approach with stack decisions
3. `/speckit-tasks` — ordered task breakdown (review-gated)
4. User reviews spec/plan/tasks and approves
5. `/speckit-implement` — execute tasks one at a time
6. Verify with: `POST /api/auth/login` → `GET /api/candidates/` → relevant feature endpoint
7. Commit granularly throughout execution

### Pre-Commit Verification
Before every commit, verify:
- DB schema matches models (PRAGMA table_info)
- No `.env` with real credentials tracked
- Model relationships have matching `back_populates` on both sides
- New endpoints have proper `Depends()` auth protection
- The app starts without import errors: `cd backend && .venv/bin/python -c "from app.main import app; print('OK')"`
- No `lazy="selectin"` on Candidate relationships

### Stale Documentation
These files are known to be stale and MUST NOT be trusted without independent verification:
| File | Known Issue |
|------|-------------|
| `FUNCTIONALITY_ISSUES.md` | Claims 6 feature modules are commented out — all 12 routers are actually live |
| `USER_ACCOUNTS.md` | Lists test accounts that are NOT pre-seeded (must be created via registration or seed.py) |

Consult `backend/app/main.py` for the ground-truth list of active routers. Consult `seed.py` for the ground-truth seed credentials (`admin@knowledgefactory.io` / `admin123`).

## Pipeline Conventions

### Candidate Status Transitions
- Statuses are additive and one-directional (forward only). No automated rollback.
- Manual override for testing: update `candidates.status` directly in DB.
- `target_statuses` filter on pipeline-stats zero-fills all requested statuses.
- Filters (branch, college, CGPA range, search, date range) are applied consistently via `apply_candidate_filters()` in `core/filters.py`.

### Analytics
- `GET /api/analytics/funnel` — real data from DB with filters
- `GET /api/analytics/dashboard` — real for totals/selection rate/CGPA/status breakdown
- Mock data still present for: `passRatePerRound` ([75, 60, 45]), `collegeBreakdown` ([]), `branchPerformance` ([]), `proctoringViolations` ([])
- New analytics endpoints MUST use real DB queries. Mock data requires a documented `// TODO` with the target implementation date.

### WebSocket
All WebSocket files in `backend/app/websockets/` are placeholders (Phase 2). No WebSocket routes are registered. Do not depend on WebSocket availability.

## Governance

### Amendment Procedure
1. Propose the change to the constitution via `/speckit-constitution` with explicit rationale.
2. Changes to Core Principles (I-VII) require user approval. Changes to Technology Stack, Development Workflow, Pipeline Conventions, or Governance may be applied with notification.
3. Version is bumped per semantic versioning:
   - MAJOR: Principle removed/redefined, backward-incompatible governance change
   - MINOR: New principle or materially expanded guidance
   - PATCH: Clarifications, fix typos, non-semantic refinements
4. After amendment, propagate changes to:
   - `.specify/templates/spec-template.md` — if scope or mandatory sections changed
   - `.specify/templates/plan-template.md` — if architecture constraints changed
   - `.specify/templates/tasks-template.md` — if task categories changed

### Compliance
- Every `/speckit-implement` run MUST reference this constitution and flag any violations.
- `/speckit-analyze` (if used) SHOULD check cross-artifact consistency against the constitution.
- Hotfixes that bypass the spec-first workflow MUST be followed by a spec amendment within 3 working days.

**Version**: 1.0.0 | **Ratified**: 2026-05-18 | **Last Amended**: 2026-05-18
