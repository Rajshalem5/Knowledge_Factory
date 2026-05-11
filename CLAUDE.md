# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Behavioral Guidelines

**These guidelines override default behavior. Tradeoff: caution over speed.**

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

Test: every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

---

## Project Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1: MVP** | Core infra — auth, DB, candidate CRUD, basic assessment flow, code execution sandbox | ~85% done — 3 known API mismatches (see Mismatches section) |
| **Phase 2: Full Pipeline** | AI evaluation, real-time proctoring (WebSocket), Celery workers, email, audit logging, analytics | 0% done — all stub files empty |
| **Phase 3: Production** | S3 uploads, security hardening, CI/CD, K8s, load testing, read replicas | Not started |

## Project Overview

Knowledge Factory is a role-based intern hiring platform with AI-powered assessments, real-time code execution, and comprehensive analytics. It consists of:

- **Frontend**: React 19 + TypeScript + Vite SPA with role-based routing
- **Backend**: FastAPI 0.115 + SQLAlchemy 2.0 async with PostgreSQL/SQLite
- **Key Features**: Multi-role access (candidate/hr/interviewer/admin/superadmin), assessment engine, code sandbox, proctoring, analytics

## Development Commands

### Frontend (React + Vite)
```bash
cd app
npm install              # Install dependencies
npm run dev             # Start dev server (http://localhost:5173)
npm run build           # TypeScript check + production build
npm run lint            # Run ESLint
npm run preview         # Preview production build
```

### Backend (FastAPI + Python)
```bash
cd backend
python -m venv venv                    # Create virtual environment
source venv/bin/activate               # Activate (Windows: venv\Scripts\activate)
pip install -r requirements.txt       # Install dependencies
alembic upgrade head                   # Run database migrations
uvicorn app.main:app --reload --port 8000  # Start dev server (http://localhost:8000)
pytest tests/                          # Run tests
```

### Database Operations
```bash
cd backend
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                             # Apply migrations
alembic downgrade -1                             # Rollback one migration
```

## Architecture Overview

### Frontend Architecture
- **SPA with client-side routing** using React Router v7
- **State management**: React Context for auth/theme, TanStack Query for server state
- **API layer**: Centralized `api` client with auto JWT injection from `localStorage.kf_token`
- **Role-based access**: `ProtectedRoute` component wraps protected routes, checks `useAuth().role`
- **Design system**: Tailwind CSS 4.2 with custom surface hierarchy and glassmorphism

### Backend Architecture
- **Clean architecture**: Routes → Services → Models → Schemas
- **Feature-based organization**: Each domain (auth, candidates, assessments, etc.) has its own module
- **Async/await throughout**: SQLAlchemy 2.0 async with PostgreSQL/SQLite
- **JWT authentication**: Role-based access control enforced at route level
- **Dependency injection**: FastAPI `Depends()` for database sessions and auth

### Key Architectural Patterns

**Frontend API Client Pattern**:
```typescript
// All API calls use the centralized api client
import { api } from './api/client';
const data = await api.get<CandidateType>('/candidates/:id');
```

**Backend Feature Structure**:
```
backend/app/features/{domain}/
├── models.py      # SQLAlchemy ORM models
├── schemas.py     # Pydantic request/response models
├── service.py     # Business logic layer
└── routes.py      # FastAPI route handlers
```

**Role-Based Access Control**:
- Frontend: `ProtectedRoute` component with `allowedRoles` prop
- Backend: Route-level decorators and dependency injection
- Roles: `candidate`, `hr`, `interviewer`, `admin`, `superadmin`

## Important Configuration

### Frontend Environment Variables (`app/.env`)
```env
VITE_API_URL=http://localhost:8000/api
VITE_ENABLE_DEMO_MODE=false
VITE_LOG_LEVEL=info
```

### Backend Environment Variables (`backend/.env`)
Currently configured for dev:
- `DATABASE_URL=sqlite+aiosqlite:///./knowledge_factory.db`
- `CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8001`
- `DEBUG=true`
- `JWT_SECRET_KEY`: Secret for JWT token signing
- `AI_API_KEY`: API key for AI question generation
- `SANDBOX_URL`: Code execution sandbox URL

### Database Configuration
- **Development**: SQLite (`aiosqlite:///./knowledge_factory.db`) — `knowledge_factory.db` exists in `backend/`
- **Production**: PostgreSQL (`postgresql+asyncpg://`) recommended
- **Migrations**: Alembic with auto-discovery of all models inheriting from `Base`
- **Virtual environment**: `backend/.venv` (Windows: `backend\.venv\Scripts\python.exe`)

## Key Development Patterns

### Adding a New Backend Feature
1. Create feature directory: `backend/app/features/{feature}/`
2. Implement models, schemas, service, routes following existing patterns
3. Import and register router in `backend/app/main.py`
4. Add models to `backend/app/main.py` startup event for discovery

### Adding a New Frontend Page
1. Create component in `app/src/pages/{section}/`
2. Add route in `app/src/App.tsx` with `ProtectedRoute` wrapper
3. Create API client functions in `app/src/api/{domain}.ts`
4. Create custom hook in `app/src/hooks/use{Domain}.ts` if needed

### Authentication Flow
1. User calls `login()` or `register()` from `AuthContext`
2. Backend validates credentials, returns JWT token + user data
3. Frontend stores `kf_token` and `kf_user` in `localStorage`
4. Subsequent API calls auto-include `Authorization: Bearer <token>` header
5. `ProtectedRoute` checks role and redirects unauthorized users

### API Error Handling
- Frontend: Centralized error handling in `api/client.ts` parses error responses
- Backend: Pydantic validation + custom exceptions in `app/core/exceptions.py`
- Consistent error format: `{"detail": "error message"}` or `{"message": "error message"}`

## Testing Approach

### Backend Testing
- **Framework**: pytest with pytest-asyncio for async tests
- **Fixtures**: Database session, async HTTP client in `tests/conftest.py`
- **Test isolation**: Each test runs in a transaction that's rolled back
- **Test database**: Separate `kf_test` database to avoid polluting dev data

### Frontend Testing
- Currently no test suite configured
- Consider adding React Testing Library for component tests
- Consider adding Playwright for E2E tests

## Common Issues and Solutions

### Frontend Issues
- **Blank page after login**: Check `ROLE_HOME_ROUTES` mapping in `app/src/utils/roles.ts`
- **401 on API calls**: Verify `localStorage.kf_token` exists and is valid
- **CORS errors**: Check `CORS_ORIGINS` in backend `.env` includes frontend URL
- **Build fails**: Run `npx tsc --noEmit` to see TypeScript errors

### Backend Issues
- **Database connection errors**: Verify `DATABASE_URL` format and database exists
- **Migration conflicts**: Use `alembic revision --autogenerate` carefully, review generated migrations
- **Import errors**: Ensure all models are imported in `app/main.py` startup event
- **Async/await errors**: All database operations must use async session and await

## Deployment Considerations

### Backend Deployment
- Use `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker` for production
- Set `DEBUG=false` in production environment
- Use PostgreSQL instead of SQLite for production
- Configure proper `JWT_SECRET_KEY` and other secrets
- Set up proper CORS origins for production frontend

### Frontend Deployment
- Build with `npm run build` for production
- Serve static files with nginx or similar
- Set `VITE_API_URL` to production backend URL
- Consider enabling HTTPS in production

## Code Quality Standards

### TypeScript/React
- Use TypeScript strict mode
- Follow existing component patterns and naming conventions
- Use TanStack Query for all server state
- Keep components focused and reusable
- Follow the established design system (colors, surfaces, typography)

### Python/FastAPI
- Use type hints throughout
- Follow async/await patterns for database operations
- Use Pydantic for all request/response validation
- Keep business logic in service layer, not in routes
- Use dependency injection for database sessions and auth

### Database
- All models inherit from `Base` in `app.database`
- Use Alembic for all schema changes
- Use async sessions for all database operations
- Follow naming conventions: snake_case for tables/columns

## Project Memory

- **Memory index**: `docs/memory/MEMORY.md`
- **Build notes**: `docs/memory/build-memory.md`
- **Design tokens**: `docs/memory/design-tokens.md`
- **File structure**: `docs/memory/file-structure.md`

## Documentation Structure

All docs live under `docs/`:
- `docs/api/` — API documentation, OpenAPI spec
- `docs/architecture/` — System architecture, platform overview
- `docs/diagrams/` — SVG sequence diagrams for each hiring round
- `docs/reports/` — Audit reports, QA findings, integration summaries
- `docs/setup/` — Setup guides, frontend quick-start, integration docs
- `docs/memory/` — Project memory and historical notes

## Integration Points

### External Services
- **AI API**: Question generation via configured AI endpoint (stub — `backend/app/integrations/ai_engine.py`)
- **Code Sandbox**: Judge0 or similar for code execution (stub — `backend/app/features/code_execution/routes.py`)
- **Email Service**: SendGrid/SES for notifications (stub — `backend/app/integrations/email.py`)
- **Object Storage**: S3-compatible for file uploads (not started — Phase 3)
- **Task Queue**: Celery + Redis for async jobs (stub — `backend/app/workers/celery_app.py`)
- **WebSockets**: Real-time proctoring/dashboard (stubs — `backend/app/websockets/`)

### Key Integrations
- **Frontend ↔ Backend**: REST API with JWT authentication
- **Backend ↔ Database**: Async SQLAlchemy 2.0
- **Assessments ↔ Code Execution**: Sandbox integration for running code (stub)
- **Proctoring ↔ Frontend**: WebSocket or polling for real-time monitoring (stub)

## Performance Considerations

### Frontend
- TanStack Query caching with 30-second stale time
- Code splitting and lazy loading for large components
- Optimistic updates for better UX
- Debounced search and filter inputs

### Backend
- Async database operations for better concurrency
- Connection pooling configured in settings
- Rate limiting on sensitive endpoints
- Efficient database queries with proper indexing

## API Route Inventory

**Base URL**: `http://localhost:8000` | **Health**: `GET /health`

| Module | Prefix | Route Count | Key Endpoints |
|--------|--------|-------------|---------------|
| Auth | `/api/auth` | 8 | login, register, me, refresh, logout, verify-otp, forgot/reset-password |
| Candidates | `/api/candidates` | 5 | list, get, me, status, bulk-upload |
| Assessment | `/api/assessment` | 3 | start, active, submit-section |
| Code Execution | `/api/code` | 3 | execute, evaluate, evaluate-question/:id |
| Questions | `/api/questions` | 2 | generate, :id/public |
| Proctoring | `/api/proctoring` | 1 | event |
| Interviews | `/api/candidates/:id/feedback` | 2 | submit feedback, get feedback |
| Selection | `/api/selection` | 3 | select, bulk-select, reject |
| Analytics | `/api/analytics` | 2 | funnel, dashboard |
| Admin/Audit | `/api/admin` | 2 | users, logs |
| Hiring Cycles | `/api/hiring-cycles` | 3 | list, create, update |
| Screening | `/api/screening` | 1 | run |
| Organizations | `/api/admin/organizations` | 3 | **Disabled (501)** — multi-tenancy removed |
| WebSockets | — | 2 | **Placeholders** — proctoring, dashboard (Phase 2) |

### Known Frontend ↔ Backend Mismatches

All previously tracked API mismatches have been fixed. See commit history for details.

### Known Integration Issues (fixed in latest commits)

1. ~~**`candidates/routes.py`** — missing `select` import in `bulk_upload_candidates`~~ ✅ Fixed — crashes at runtime with `NameError: name 'select' is not defined` when active cycle check runs
2. ~~**`SelectionPanel.tsx`** — filter checks `c.status` instead of `c.display_status`~~ ✅ Fixed — `status` contains raw backend enum (`INTERVIEW_COMPLETED`) which never matches simplified display strings (`interviewed`)
3. ~~**`CandidateDetail.tsx`** — `InterviewRecommendation.HOLD` shows as "Reject"~~ ✅ Fixed — now shows "Hold" with warning badge
4. ~~**`from_orm_compat()`** — `proctoring_flags` never populated~~ ✅ Fixed — added `back_populates` relationship between Candidate and ProctoringRecord, builds flags from `violations_json`
5. ~~**`InterviewPanel.tsx`** — only Select/Reject buttons, missing Hold option~~ ✅ Fixed — added Hold button with warning styling
6. ~~**`candidates.ts`** — `previewBulkUpload()` calls `/bulk-upload/preview`~~ ✅ Fixed — backend route added (commit `e181541`)
7. ~~**`assessment.ts`** — `getAssessment()` had double `/api` prefix~~ ✅ Fixed (commit `eb7a0df`)
8. ~~**Backend CandidateStatus (ROUND1_PASSED etc) vs Frontend CandidateStatus (eligible, round1 etc)** — mismatched status enums broke display and status updates~~ ✅ Fixed — added `display_status` property and `from_display_status()` classmethod to `CandidateStatus` enum, added `display_status` field to `CandidateRead` schema, patched frontend components to use `display_status` (commit `d5ba312`)

### Pipeline Status

| Component | Status | Notes |
|-----------|--------|-------|
| Screening (POST /api/screening/run) | ✅ Complete | Transitions APPLIED → ROUND1_PASSED/ROUND1_REJECTED, supports extra filters |
| Pipeline Stats (GET /api/screening/pipeline-stats) | ✅ Complete | Aggregated counts per candidate status |
| Assessment Start (POST /api/assessment/start) | ✅ Complete | Validates candidate must be ROUND1_PASSED (for ROUND_2) or ROUND2_PASSED (for ROUND_3), transitions via FSM |
| Candidate Listing (GET /api/candidates) | ✅ Enhanced | Supports branch, college, cgpa_min, cgpa_max, passed_out_year filters |
| Status Update (PATCH /api/candidates/{id}/status) | ✅ Complete | Accepts both backend enum and simplified frontend status values |
| HR Dashboard "Run Screening" button | ✅ Added | Triggers screening, shows pipeline stats |
| Candidate Portal "Start Assessment" button | ✅ Added | Starts assessment via API, transitions status, navigates to /assessment |

| ### Known TODO
|
| - (none — all Phase 1 known issues resolved)

## Security Notes

- JWT tokens stored in `localStorage` — httpOnly cookies implemented for refresh tokens (P0-3), consider migrating access tokens too for production
- Role-based access control enforced on both frontend and backend
- Input validation via Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
- CORS properly configured for allowed origins
- File upload validation and type checking
- Rate limiting on authentication and code execution endpoints