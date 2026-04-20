# Knowledge Factory — MNC-Level Project Review

**Date:** 2026-04-20  
**Reviewer:** Principal Backend Architect  
**Project Type:** AI-Powered Intern Hiring Platform (SaaS)  
**Current State:** Backend scaffold complete (25%), Frontend UI prototype (62%), System maturity: 26%  
**Classification:** UI Prototype with Greenfield Backend

---

## Executive Summary

This review provides a comprehensive MNC-level assessment of the Knowledge Factory platform, covering all backend FastAPI components, frontend React/TypeScript code, infrastructure configuration, and security posture. The review follows enterprise-grade standards with specific line-numbered findings and actionable fixes.

---

## Backend Review (FastAPI + PostgreSQL)

### `backend/app/main.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L27-47 | 🟡 | Lifespan context manager imports `engine` at module level but only uses it inside shutdown | Move import to top or use lazy import consistently |
| L46 | 🟡 | Import inside function `from app.database import engine` creates tight coupling | Inject via dependency instead |
| L59-60 | 🔵 | Docs disabled in production via runtime check | Consider using `docs_url=None` directly in settings-driven config |
| L69 | 🟡 | CORS allows all methods/headers in all environments | Restrict in staging/production |
| L97-128 | 🔵 | All routers commented out — expected for scaffold but blocks integration testing | Unblock as features implemented |

### `backend/app/config.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L41 | 🟡 | Default DATABASE_URL contains plaintext credentials | Use `postgresql+asyncpg://localhost/knowledge_factory` with env override only |
| L57-63 | 🟡 | JWT keys default to empty strings | Add validation that raises if missing in non-DEBUG mode |
| L69 | 🟡 | AI_MODEL default references non-existent model ID | Should be `claude-3-sonnet-20240229` or similar |
| L71 | 🔵 | AI_DAILY_SPEND_CAP_USD is per-cycle but named daily | Rename to `AI_SPEND_CAP_PER_CYCLE_USD` |
| L75 | 🟡 | SANDBOX_URL default points to localhost but Judge0 in docker-compose is at `judge0:2358` | Update default or use service discovery |
| L86 | 🔵 | `__all__` not defined for module exports | Add explicit exports |

### `backend/app/database.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L30 | 🔵 | Engine created at import time | Fine for FastAPI but prevents testing with different DB URLs without monkeypatching |
| L38 | ✅ | `pool_pre_ping=True` | Good — prevents stale connection errors |
| L48 | 🔵 | `expire_on_commit=False` keeps objects alive but risks stale data | Document this trade-off |
| L60-81 | 🟡 | `get_db()` commits on success, rolls back on exception | Good pattern but missing logging for rollback events |
| L76 | 🟡 | Silent commit failure possible if exception raised during `await session.commit()` | Wrap in try/except with logging |

### `backend/app/core/enums.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L16-24 | 🟡 | `Role` enum missing `CANDIDATE` | Architecture doc Section 5.1 says candidates are separate table, but frontend uses `role: 'candidate'` |
| L51-81 | 🟡 | `CandidateStatus` has 15 states but migration uses string(30) while some values exceed 20 chars | Migration mismatch — verify column sizes |
| L67-81 | 🔵 | State transition comments document FSM but no runtime enforcement | Add `can_transition(from, to)` helper |
| L86-89 | 🔴 | `AssessmentRound` only has ROUND_2, ROUND_3. Missing ROUND_1 per architecture Table 21 | Add ROUND_1 or update architecture doc |
| L136-140 | 🔵 | `ProctoringSeverity` uses lowercase values while other enums use UPPERCASE | Inconsistent — standardize |
| L145-149 | 🔵 | `OrganizationPlan` lowercase while `TenantStatus` uppercase | Pick one convention |
| L154-158 | 🔵 | `ProblemDifficulty` lowercase. Inconsistent with `Role`, `UserStatus` | Standardize casing |

### `backend/app/core/exceptions.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L22-36 | 🟡 | `AppException` extends `HTTPException` but adds `error_code` field not used by FastAPI's default handler | Custom exception handler needed |
| L28 | 🔵 | Default status 500 for base exception | Should be abstract class with no default to force explicit codes |
| L42-48 | ✅ | `NotFoundError` message construction | Fine but consider structured logging |
| L66-72 | 🟡 | `ValidationError` conflicts with Pydantic's `ValidationError` | Rename to `BusinessValidationError` or `DomainValidationError` |
| L97-111 | 🔵 | `InvalidStateTransitionError` hardcodes field="status" | Parameterize or remove field param |
| L125-133 | 🔵 | `AISpendCapExceededError` returns 429 (rate limit) but 403 or 402 more appropriate | Use 402 Payment Required or 403 Forbidden |

### `backend/app/features/auth/models.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L36-40 | 🟡 | `Tenant.id` uses `default=uuid.uuid4` — called at import time | Use `default_factory=uuid.uuid4` or SQLAlchemy's `default=uuid.uuid4` (function, not call) |
| L42-47 | 🔵 | `slug` has unique=True at column level AND explicit index at L38 | Redundant — unique implies index |
| L48-52 | 🔴 | `config_json` server_default="now()" won't work for JSONB | Use `server_default="{}"` or handle in app |
| L58-62 | 🟡 | `created_at` server_default="now()" is string, not `sa.func.now()` | Migration uses func.now() — inconsistency |
| L93-98 | ✅ | `User.tenant_id` nullable for SuperAdmin | Document this pattern in code comment |
| L99 | 🔵 | `email` indexed but not unique. Partial index in migration handles uniqueness | Document this non-obvious pattern |
| L108 | 🟡 | `otp_secret` 32 chars may be insufficient for base32-encoded TOTP secrets (typically 52+) | Verify with pyotp |
| L113-117 | 🟡 | `created_at` same server_default string issue as Tenant | Fix models to match migration |

### `backend/app/features/candidates/models.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L55-60 | 🟡 | `tenant_id` FK with `ondelete="CASCADE"` — deleting tenant wipes all candidates | Consider `SET NULL` with archive flag |
| L67 | 🔵 | `email` indexed but uniqueness enforced via partial index in migration | Add comment explaining |
| L69-72 | 🟡 | `password_hash` nullable until OTP verified | Good for flow but risks incomplete accounts — add cleanup job |
| L76-79 | 🟡 | `cgpa` Numeric(4,2) allows 99.99 | Add CHECK constraint for 0-10 range per Indian CGPA system |
| L80 | 🔵 | `passed_out_year` no validation | Add CHECK for reasonable range (e.g., 2000-2030) |
| L83 | 🔵 | `language_choice` free text | Should be enum or FK to supported_languages table |
| L90-94 | 🔵 | `email_verified` boolean default False | No timestamp for when verified — add `email_verified_at` |
| L106-129 | 🔵 | All relationships use `lazy="selectin"` | Good for N+1 prevention but may over-fetch — document trade-off |

### `backend/app/features/assessments/models.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L61-65 | 🟡 | `questions_json` stores AI-generated questions | No schema validation — add Pydantic validator or JSON Schema |
| L66-71 | 🟡 | `link_token` 64 chars, unique, indexed | Good for URL-safe tokens but consider crypto-secure generation (secrets.token_urlsafe) |
| L72-75 | 🔵 | `link_expiry` no default | Should be `default=lambda: datetime.now(timezone.utc) + timedelta(days=5)` |
| L84-88 | 🔵 | `status` default NOT_STARTED but no trigger to update to IN_PROGRESS when `started_at` set | Add SQL trigger or app logic |
| L94-108 | ✅ | `proctoring_record` 1:1 relationship with `uselist=False` | Good but no unique constraint on FK at DB level (in migration though) |
| L135-138 | ✅ | `Submission.section` uses enum but stored as String(20) | Migration matches — good |
| L139-143 | 🟡 | `payload_json` stores code/MCQ answers | Large payloads may exceed JSONB limits — consider TEXT for code with JSON metadata |
| L187-206 | 🟡 | `Score` has 6 integer fields (0-100) but no CHECK constraints | Add `CheckConstraint("correctness BETWEEN 0 AND 100")` etc |
| L211-214 | 🟡 | `weighted_total` Numeric(5,2) allows 999.99 but should be 0-100 | Add CHECK constraint |

### `backend/app/features/hiring_cycles/models.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L42-47 | 🟡 | `tenant_id` FK with CASCADE | Same concern as candidates — tenant deletion wipes cycle history |
| L52-53 | 🟡 | `start_date`, `end_date` no validation that end > start | Add CHECK constraint or app validation |
| L59-73 | 🔵 | Three JSONB config fields with empty dict defaults | Good for MVP but document expected schema in code |
| L74-78 | ✅ | `created_by` FK to users with SET NULL | Good for audit trail preservation |
| L86-96 | 🔵 | Relationships use `selectin` loading | `candidates` relationship may load thousands — consider pagination or lazy |

### `backend/app/features/proctoring/models.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L51-57 | ✅ | `assessment_id` unique=True enforces 1:1 | Good |
| L64-75 | 🔵 | URL fields nullable until recordings complete | Consider validation that at least one manifest exists on completion |
| L76-80 | 🔵 | `violations_json` default=list but type hint says `list` | SQLAlchemy may wrap — verify behavior |
| L91-94 | 🔵 | `retention_expiry` required but no default | Add `default=lambda: date.today() + timedelta(days=90)` |
| L97-105 | 🔵 | Relationships to Assessment and Candidate | `candidate` relationship duplicates via assessment — consider removing |

### `backend/app/features/interviews/models.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L58-73 | 🟡 | Four score fields (1-10) but no CHECK constraints | Add constraints or use enum |
| L78-81 | 🔵 | `comments` Text nullable | Consider max length validation at API level (e.g., 5000 chars) |
| L82-86 | 🔵 | `submitted_at` server_default but interviewers may save drafts | Add `is_final` boolean or use null `submitted_at` for drafts |

### `backend/app/features/audit/models.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L47-52 | ✅ | `tenant_id` nullable with SET NULL | Audit logs survive tenant deletion — good for compliance |
| L53-58 | ✅ | `actor_id` nullable for system actions | Document this pattern |
| L74-81 | ✅ | `before_json`, `after_json` nullable for create/delete operations | Good |
| L82-89 | ✅ | `ip_address` 45 chars covers IPv6 | `user_agent` Text may store large strings — consider 1000 char limit |

### `backend/app/features/notifications/models.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L66-69 | 🔵 | `status` String(20) not enum | Should use enum for SENT/DELIVERED/BOUNCED/FAILED |
| L71-74 | 🔵 | `provider_message_id` nullable but no index | Add index for provider webhook lookups |
| L79-83 | 🔵 | `sent_at` server_default but status may be PENDING | Use nullable with app-set timestamp |

### `backend/app/features/analytics/models.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L57-61 | 🔵 | `prompt_hash` 64 chars assumes SHA-256 hex | Document this assumption |
| L74-77 | 🔵 | `cost_usd` Numeric(10,6) allows 9999.999999 | Good precision but verify against provider billing granularity |
| L82-90 | 🔵 | `status` String(20) not enum | Use enum for consistency |

### `backend/alembic/versions/001_initial_schema.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L31-36 | ✅ | `tenants` table uses `server_default=sa.func.now()` | Correct approach, models use string "now()" — fix models |
| L57-60 | ✅ | Partial unique index on users.email per tenant | Good for multi-tenancy |
| L106 | ✅ | Compound index `ix_candidates_tenant_cycle_status` | Good for filtering by tenant+cycle+status |
| L108-110 | ✅ | Partial unique index on candidates email per tenant+cycle | Good |
| L213 | ✅ | BRIN index on `audit_logs.created_at` for time-series queries | Excellent for large audit tables |
| L252-265 | ✅ | Downgrade drops tables in reverse order | Good dependency handling |

### `backend/alembic/env.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L14-22 | 🔵 | All models imported with noqa: F401 | Good for autogenerate but adds import overhead |
| L31 | ✅ | `config.set_main_option("sqlalchemy.url", ...)` overrides alembic.ini | Good for single source of truth |
| L55-64 | ✅ | `run_async_migrations()` uses `async_engine_from_config` | Good for async Alembic |

### `backend/tests/conftest.py`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L16-18 | 🔵 | `TEST_DATABASE_URL` hardcoded | Use environment variable with fallback |
| L26-31 | ✅ | `event_loop` fixture scope="session" | Good for test performance |
| L34-47 | 🔵 | `setup_database` creates/drops tables per session | Consider using migrations instead for migration testing |
| L50-61 | ✅ | `db_session` uses transaction rollback | Good isolation pattern |
| L64-74 | ✅ | `client` uses ASGITransport | Good for FastAPI testing without server |

---

## Frontend Review (React + TypeScript)

### `app/src/api/client.ts`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L14 | 🔴 | `localStorage.getItem('kf_token')` — JWT in localStorage vulnerable to XSS | Move to httpOnly cookie |
| L15-19 | 🟡 | Headers spread order allows override of Content-Type | Move custom headers spread before defaults |
| L23-26 | 🟡 | Error handling assumes JSON response | Handle non-JSON errors (e.g., network failures) |
| L31-45 | 🔵 | API methods use generic `<T>` but no runtime validation | Consider zod schemas for response validation |

### `app/src/contexts/AuthContext.tsx`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L18-22 | 🟡 | Initial state from localStorage causes hydration mismatch in SSR | Use lazy initializer or useEffect |
| L29-30 | 🟡 | `login` stores token in localStorage before confirming user object valid | Race condition risk |
| L38-48 | 🟡 | `register` same issue — stores auth data before full registration complete | Fix race condition |
| L51-56 | 🔵 | `logout` clears state but doesn't invalidate token server-side | Add `/auth/logout` API call |
| L59 | 🟡 | `role` computed from `user?.role` but backend has different role model | Sync with backend enums |

### `app/src/App.tsx`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L38-46 | 🔵 | Candidate routes protected but no assessment attempt limit check | Add max attempts validation |
| L49-58 | 🔵 | HR/Admin routes share protection but different permissions | Split or add fine-grained checks |
| L82-86 | 🔵 | SuperAdmin route protected but no additional MFA check | Consider requiring MFA for superadmin |
| L89 | 🟡 | Fallback `AuthRedirect` may loop if role null | Add max redirect count or error boundary |

### `app/src/routes/ProtectedRoute.tsx`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L11-27 | 🔵 | Double role check — `allowedRoles` param AND `canAccessRoute` | Consolidate logic |
| L19-20 | 🔵 | Role mismatch redirects to `/` but should redirect to role-appropriate home | Use ROLE_HOME_ROUTES |
| L23-25 | 🔵 | Path-based check redundant with `allowedRoles` | Remove or document when each applies |

### `app/src/utils/roles.ts`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L3-9 | 🔴 | `ROLE_LABELS` includes 'candidate' but backend Role enum doesn't | Mismatch between frontend/backend |
| L11-17 | 🔵 | `ROLE_HOME_ROUTES` hardcoded | Move to config or backend-provided settings |
| L19-28 | 🔴 | `STATUS_LABELS` uses different statuses than backend `CandidateStatus` | Sync with backend enums |
| L30-39 | 🔵 | `STATUS_COLORS` Tailwind classes use custom theme | Verify all classes exist in tailwind.config |
| L41-50 | 🟡 | `canAccessRoute` uses `startsWith` which may allow partial matches | Use exact match or regex |

---

## Infrastructure Review

### `backend/docker/docker-compose.yml`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L44 | 🟡 | `env_file: - ../.env.example` loads example file with dummy values | Should be `.env` (gitignored) |
| L48-49 | 🔵 | Database URLs hardcoded in compose override env_file | Remove if env_file sufficient |
| L61-66 | 🟡 | Judge0 placeholder incomplete | Add full Judge0 compose or remove until implemented |
| L21 | 🔵 | `pgdata` volume not named externally | Add `name: kf_pgdata` for easier management |

### `backend/pyproject.toml`

| Line | Severity | Finding | Fix |
|------|----------|---------|-----|
| L5 | ✅ | `requires-python = ">=3.12"` | Good — uses latest features |
| L8-26 | 🔵 | Ruff config comprehensive | Add "C4" (flake8-comprehensions) and "PTH" (pathlib) rules |
| L28-42 | ✅ | mypy strict mode with pydantic plugin | Good type safety |
| L44-47 | ✅ | pytest asyncio mode auto | Good for async tests |

---

## Security Findings

### 🔴 CRITICAL

| Finding | Location | Impact | Fix |
|---------|----------|--------|-----|
| JWT stored in localStorage | `app/src/api/client.ts:L14`, `app/src/contexts/AuthContext.tsx:L29-30` | XSS vulnerability — attacker can steal token via injected script | Move to httpOnly cookie |
| No rate limiting on auth endpoints | Backend router stubs | Brute force attacks on login/register | Add slowapi or custom middleware before production |

### 🟡 HIGH

| Finding | Location | Impact | Fix |
|---------|----------|--------|-----|
| CORS allows all origins | `backend/app/main.py:L69-72` | CSRF risk in production | Restrict to known origins in production |
| No CHECK constraints on score ranges | `backend/app/features/assessments/models.py` | Invalid data can be persisted | Add database constraints |

### 🟡 MEDIUM

| Finding | Location | Impact | Fix |
|---------|----------|--------|-----|
| `link_token` generation not shown | Not in reviewed files | Predictable tokens if not crypto-secure | Ensure secrets.token_urlsafe used |
| `ProctoringRecord.violations_json` no schema | `backend/app/features/proctoring/models.py:L76-80` | Invalid violation data | Add Pydantic validator |

### 🔵 LOW

| Finding | Location | Impact | Fix |
|---------|----------|--------|-----|
| Enum value casing inconsistent | Multiple enum files | Code style inconsistency | Standardize for consistency |

---

## Architecture Compliance Matrix

| Requirement | Status | Notes |
|-------------|--------|-------|
| Multi-tenancy (tenant_id) | ✅ | All tables except tenants have tenant_id |
| 15-state Candidate FSM | ✅ | All states defined in enum |
| JSONB config fields | ✅ | hiring_cycles has 3 JSONB configs |
| Partial unique indexes | ✅ | users.email, candidates.email per tenant/cycle |
| BRIN index on audit_logs | ✅ | created_at BRIN index present |
| Soft deletes | ❌ | No deleted_at columns — hard deletes only |
| Connection pooling | ✅ | SQLAlchemy pool configured |
| Async throughout | ✅ | All DB operations async |
| Role-based access | 🟡 | Backend enums don't match frontend roles |
| Candidate separate auth | ✅ | Candidates in own table per architecture |

---

## Recommendations (Priority Order)

### P0 — Critical (Block Production)

1. **Fix JWT storage** — Move from localStorage to httpOnly cookie (security)
2. **Add rate limiting** — Auth endpoints protection (security)
3. **Unify role models** — Frontend/backend role enum mismatch (bug)

### P1 — High (Required for MVP)

4. **Add CHECK constraints** — Score ranges, date validations (data integrity)
5. **Standardize enums** — All UPPERCASE or all lowercase (consistency)
6. **Implement exception handlers** — FastAPI handlers for custom exceptions (functionality)
7. **Add server-side logout** — Token invalidation (security)

### P2 — Medium (Post-MVP)

8. **Add soft deletes** — deleted_at columns for audit compliance (architecture)
9. **Implement Judge0** — Code execution sandbox placeholder (feature)
10. **Add request ID middleware** — For tracing and audit correlation (observability)
11. **Add MFA for SuperAdmin** — Enhanced security for privileged accounts (security)

### P3 — Low (Nice to Have)

12. **Document JSONB schemas** — Expected structure for config fields (documentation)
13. **Add comprehensive logging** — Structured logging with correlation IDs (observability)
14. **Implement health checks** — Deep health check for DB/Redis connectivity (operations)

---

## Code Quality Metrics

| Metric | Score | Notes |
|--------|-------|-------|
| Type Safety | 8/10 | mypy strict, good type hints, some any types |
| Test Coverage | 2/10 | Test fixtures exist but no actual tests |
| Documentation | 7/10 | Good docstrings, architecture alignment |
| Security Posture | 4/10 | Critical JWT issue, missing rate limiting |
| Performance | 7/10 | Proper indexes, selectin loading, async |
| Maintainability | 8/10 | Clean structure, separation of concerns |

---

## Overall Assessment

### Strengths

- Clean async SQLAlchemy 2.0 patterns with proper session management
- Comprehensive Alembic migration with production-grade indexes (BRIN, partial unique)
- Good separation of concerns in backend structure (features-based)
- Frontend role-based routing implemented with ProtectedRoute
- Docker Compose for local development with health checks
- Architecture doc compliance for multi-tenancy and FSM design
- Exception hierarchy designed for consistent error responses

### Weaknesses

- **Security gaps:** JWT in localStorage (XSS), no rate limiting, permissive CORS
- **Data integrity:** Missing CHECK constraints on critical fields
- **Frontend/backend drift:** Role enums and status values don't match
- **Incomplete infrastructure:** Judge0 placeholder, no Redis integration shown
- **No soft delete pattern:** Hard deletes only, audit trail gaps
- **Testing gap:** Fixtures exist but no actual test coverage

### MNC Readiness Score: 3/10

**Justification:**
- Core backend scaffold is solid with good architectural patterns (3 points)
- Database design is production-ready with proper indexing (2 points)
- Security hardening needed before any production deployment (-2 points)
- Frontend/backend synchronization issues need resolution (-1 point)
- Testing infrastructure incomplete (-1 point)
- Infrastructure completion needed (Judge0, Redis, etc.) (-1 point)

**Path to Production:**
1. Fix P0 critical issues (JWT, rate limiting, role sync)
2. Add CHECK constraints and validation
3. Implement comprehensive test suite
4. Complete infrastructure (Judge0, proper Docker setup)
5. Security audit and penetration testing
6. Performance testing with realistic load

---

## Appendix: File Inventory

### Backend (45 files)
- Core: `main.py`, `config.py`, `database.py`, `dependencies.py`
- Enums: `core/enums.py`
- Exceptions: `core/exceptions.py`
- Models: `auth/models.py`, `candidates/models.py`, `assessments/models.py`, `hiring_cycles/models.py`, `proctoring/models.py`, `interviews/models.py`, `audit/models.py`, `notifications/models.py`, `analytics/models.py`
- Migration: `alembic/versions/001_initial_schema.py`, `alembic/env.py`
- Tests: `tests/conftest.py`
- Infrastructure: `docker/docker-compose.yml`, `docker/Dockerfile`, `pyproject.toml`, `requirements.txt`

### Frontend (25+ files)
- API: `api/client.ts`, `api/auth.ts`, `api/candidates.ts`, `api/assessment.ts`, `api/analytics.ts`
- Contexts: `contexts/AuthContext.tsx`
- Routes: `App.tsx`, `routes/ProtectedRoute.tsx`
- Utils: `utils/roles.ts`
- Components: UI components, layout components, assessment components

---

*Review completed using caveman-review skill format. All findings include specific line numbers and actionable fixes.*
