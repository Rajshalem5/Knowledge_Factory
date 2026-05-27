# API Documentation Audit & Health Report

## 1. Route Inventory Table

| Method | Endpoint | Module | Status | Purpose |
| ------ | -------- | ------ | ------ | ------- |
| POST | `/api/auth/login` | `auth` | ✅ Working | Authenticate user/candidate and return tokens. |
| POST | `/api/auth/register` | `auth` | ✅ Working | Register a new candidate for the active hiring cycle. |
| GET | `/api/auth/me` | `auth` | ✅ Working | Get current authenticated user/candidate profile. |
| POST | `/api/auth/refresh` | `auth` | ✅ Working | Refresh access token using cookie-based refresh token. |
| POST | `/api/auth/logout` | `auth` | ✅ Working | Logout and clear refresh token cookie. |
| GET | `/api/candidates/` | `candidates` | ✅ Working | List all candidates with extensive filtering. |
| POST | `/api/candidates/me/resume` | `candidates` | ✅ Working | Upload and AI-parse candidate resume. |
| GET | `/api/candidates/me` | `candidates` | ✅ Working | Get authenticated candidate's profile. |
| GET | `/api/candidates/{id}` | `candidates` | ✅ Working | Get candidate details by ID (HR/Admin). |
| PATCH | `/api/candidates/{id}/status` | `candidates` | ✅ Working | Update candidate pipeline status. |
| POST | `/api/candidates/bulk-upload/preview` | `candidates` | ✅ Working | Preview bulk upload data. |
| POST | `/api/candidates/bulk-upload` | `candidates` | ✅ Working | Bulk upload candidates from CSV/PDF/DOCX. |
| GET | `/api/candidates/{id}/resume` | `candidates` | ✅ Working | Download candidate resume file. |
| GET | `/api/assessment/{id}/admin` | `assessments` | ✅ Working | Get full assessment details for admin review. |
| POST | `/api/assessment/start` | `assessments` | ✅ Working | Start an assessment round for a candidate. |
| GET | `/api/assessment/active` | `assessments` | ✅ Working | Get active assessments for current candidate. |
| POST | `/api/assessment/{id}/complete` | `assessments` | ✅ Working | Mark assessment as completed. |
| GET | `/api/assessment/{id}/result` | `assessments` | ✅ Working | Get result summary for an assessment. |
| GET | `/api/assessment/{id}` | `assessments` | ✅ Working | Get assessment details by ID. |
| POST | `/api/assessment/submit-section` | `assessments` | ✅ Working | Submit answers for an assessment section. |
| POST | `/api/code/execute` | `code_exec` | ✅ Working | Run code with custom stdin via Piston. |
| POST | `/api/code/evaluate` | `code_exec` | ✅ Working | Evaluate code against test cases. |
| POST | `/api/code/evaluate-question/{id}` | `code_exec` | ✅ Working | Evaluate code against question test cases. |
| POST | `/api/questions/generate` | `questions` | ✅ Working | Generate coding question via AI. |
| GET | `/api/questions/{id}/public` | `questions` | ✅ Working | Get public view of a question. |
| POST | `/api/proctoring/session` | `proctoring` | ✅ Working | Initialize proctoring session and get WS token. |
| POST | `/api/proctoring/webhook/event` | `proctoring` | ⚠ Risk | Webhook for AI service to report violations. |
| POST | `/api/proctoring/terminate/{id}` | `proctoring` | ✅ Working | Terminate a proctoring session. |
| GET | `/api/proctoring/assessment/{id}/session` | `proctoring` | ✅ Working | Get session for an assessment. |
| GET | `/api/proctoring/session/{id}/status` | `proctoring` | ✅ Working | Get current session status. |
| GET | `/api/proctoring/session/{id}/events` | `proctoring` | ✅ Working | List all session events. |
| GET | `/api/proctoring/session/{id}/evidence` | `proctoring` | ✅ Working | List session evidence (screenshots). |
| POST | `/api/candidates/{id}/feedback` | `interviews` | ✅ Working | Submit interviewer feedback. |
| GET | `/api/candidates/{id}/feedback` | `interviews` | ✅ Working | Get candidate interview feedback. |
| GET | `/api/selection/ranking/{id}` | `selection` | ✅ Working | Get ranked candidates for a cycle. |
| POST | `/api/selection/candidates/{id}/decision` | `selection` | ✅ Working | Make final hiring decision. |
| POST | `/api/selection/candidates/{id}/select` | `selection` | ✅ Working | Convenience wrapper for selection. |
| POST | `/api/selection/candidates/{id}/reject` | `selection` | ✅ Working | Convenience wrapper for rejection. |
| GET | `/api/analytics/funnel` | `analytics` | ✅ Working | Get hiring funnel statistics. |
| GET | `/api/analytics/dashboard` | `analytics` | ✅ Working | Get high-level dashboard metrics. |
| GET | `/api/admin/users` | `admin` | ✅ Working | List platform users. |
| POST | `/api/admin/users` | `admin` | ✅ Working | Create a new platform user. |
| PATCH | `/api/admin/users/{id}` | `admin` | ✅ Working | Update user details. |
| DELETE | `/api/admin/users/{id}` | `admin` | ✅ Working | Delete a user. |
| GET | `/api/admin/logs` | `audit` | ✅ Working | Retrieve audit logs. |
| GET | `/api/hiring-cycles/` | `cycles` | ✅ Working | List hiring cycles. |
| POST | `/api/hiring-cycles/` | `cycles` | ✅ Working | Create a new hiring cycle. |
| PATCH | `/api/hiring-cycles/{id}` | `cycles` | ✅ Working | Update hiring cycle config. |
| POST | `/api/screening/run` | `screening` | ✅ Working | Run auto-screening on candidates. |
| GET | `/api/screening/pipeline-stats` | `screening` | ✅ Working | Get candidate counts per stage. |
| WSS | `/ws/proctor/{id}` | `ws` | ✅ Working | Real-time proctoring data stream. |
| GET | `/health` | `main` | ✅ Working | API health check. |
| POST | `/jobs/` | `jobs` | ❌ Broken | Missing router inclusion; uses Postgres-only SQL. |
| POST | `/phase2/start/{id}` | `phase2` | ❌ Broken | Missing router inclusion; uses Postgres-only SQL. |

---

## 2. Working Endpoints List
All endpoints prefixed with `/api` and listed in `main.py` are considered working as they follow the project's standard pattern, have complete service logic, and no obvious syntax/runtime issues in their core paths.

## 3. Broken / Unreachable Endpoints
- **Jobs Module (`/jobs/`):** The router is not included in `app/main.py`. Additionally, the implementation uses `NOW()` and `RETURNING` clauses in raw SQL which are not natively supported by SQLite in the same way (or might require custom definitions).
- **Phase 2 Module (`/phase2/`):** Not included in `main.py`. Uses `now()` in raw SQL.
- **SuperAdmin Module:** Not included in `main.py`. Redundant with `admin` module.

## 4. Frontend-to-Backend Mapping
| Frontend API Client | Backend Endpoint Prefix | Status |
| ------------------- | ----------------------- | ------ |
| `auth.ts` | `/api/auth` | ✅ Linked |
| `candidates.ts` | `/api/candidates` | ✅ Linked |
| `assessment.ts` | `/api/assessment` | ✅ Linked |
| `code-execution.ts` | `/api/code` | ✅ Linked |
| `questions.ts` | `/api/questions` | ✅ Linked |
| `proctoring.ts` | `/api/proctoring` | ✅ Linked |
| `interview.ts` | `/api/candidates/{id}/feedback` | ✅ Linked |
| `selection.ts` | `/api/selection` | ✅ Linked |
| `analytics.ts` | `/api/analytics` | ✅ Linked |
| `admin.ts` | `/api/admin` | ✅ Linked |
| `hiring-cycles.ts` | `/api/hiring-cycles` | ✅ Linked |
| `screening.ts` | `/api/screening` | ✅ Linked |
| `jobs.ts` | `/jobs` | ❌ Broken (Prefix mismatch & Missing Router) |
| `phase2.ts` | `/phase2` | ❌ Broken (Prefix mismatch & Missing Router) |

---

## 5. Authentication Matrix
| Endpoint Group | Auth Type | Allowed Roles |
| -------------- | --------- | ------------- |
| `/api/auth/login`, `/register` | Public | All |
| `/api/candidates/me` | JWT | Candidate |
| `/api/candidates/` (List) | JWT | Admin, HR, SuperAdmin |
| `/api/assessment/start` | JWT | Candidate |
| `/api/admin/*` | JWT | Admin, SuperAdmin |
| `/api/analytics/*` | JWT | Admin, HR, SuperAdmin |
| `/api/proctoring/webhook` | None | (Risk) |

---

## 6. Recommended Fixes
1. **Include Missing Routers:** Add `jobs` and `phase2` to `app/main.py` if they are intended to be part of the product.
2. **Fix SQL Dialects:** Replace `now()` or `NOW()` with `datetime('now')` or use SQLAlchemy's `func.now()` for portability.
3. **Unified Prefixes:** Ensure frontend `jobs.ts` and `phase2.ts` use the `/api/` prefix to match the rest of the application.
4. **Secure Webhooks:** Add a secret key validation for `/api/proctoring/webhook/event`.
5. **OTP Hardening:** Replace dev-mode OTP auto-acceptance with actual verification for production.
