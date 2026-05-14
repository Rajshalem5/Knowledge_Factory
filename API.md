# Knowledge Factory — API Reference

> **Base URL:** `http://localhost:8000` (development)  
> **Auth:** JWT Bearer token (`Authorization: Bearer <token>`)  
> **Interactive Docs:** `/docs` (Swagger UI) or `/redoc` (ReDoc) — available when `DEBUG=true`  
> **Frontend proxy:** Vite dev server proxies `/api/*` → backend at `VITE_API_URL`

---

## Table of Contents

- [Authentication](#1-authentication-api-auth)
- [Candidates](#2-candidates-api-candidates)
- [Assessments](#3-assessments-api-assessment)
- [Code Execution](#4-code-execution-api-code)
- [Questions](#5-questions-api-questions)
- [Proctoring](#6-proctoring-api-proctoring)
- [Interviews](#7-interviews-api)
- [Selection](#8-selection-api-selection)
- [Analytics](#9-analytics-api-analytics)
- [Admin](#10-admin-api-admin)
- [Hiring Cycles](#11-hiring-cycles-api-hiring-cycles)
- [Screening](#12-screening-api-screening)
- [Health](#13-health-get-health)
- [Unregistered Routes (not wired)](#14-unregistered-routes)

---

## 1. Authentication (`/api/auth`)

### POST `/api/auth/login`
Authenticate user or candidate. Returns access token + sets httpOnly refresh cookie.

**Request:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "string", "name": "string", "role": "string" }
}
```

### POST `/api/auth/register`
Register a new candidate. Auto-assigns to active hiring cycle.

**Request:**
```json
{
  "email": "string",
  "password": "string",
  "name": "string"
}
```

**Response (201):** Returns access_token, refresh_token, token_type, and user object.

### GET `/api/auth/me`
Get current user profile from JWT token.

**Response (200):**
```json
{ "id": "uuid", "email": "string", "name": "string", "role": "string" }
```

### POST `/api/auth/refresh`
Refresh access token using the httpOnly refresh cookie. Reads `kf_refresh_token` cookie automatically.

**Response (200):**
```json
{ "access_token": "string", "token_type": "bearer" }
```

### POST `/api/auth/logout`
Clears the httpOnly refresh cookie.

**Response (200):** `{ "message": "Logged out" }`

### POST `/api/auth/verify-otp`
Verify OTP for email verification. Dev mode auto-accepts any 6-digit code.

**Request:**
```json
{ "email": "string", "otp": "string" }
```

**Response (200):** Full TokenResponse with access_token, refresh_token, user.

### POST `/api/auth/forgot-password`
Request password reset — generates token (email sending is a TODO placeholder).

**Request:**
```json
{ "email": "string" }
```

**Response (200):** `{ "message": "If email exists, a reset link has been sent." }`

### POST `/api/auth/reset-password`
Reset password using a valid reset token.

**Request:**
```json
{
  "token": "string",
  "new_password": "string"
}
```

**Response (200):** `{ "message": "Password has been reset successfully." }`

---

## 2. Candidates (`/api/candidates`)

**Auth:** Most endpoints require `HR`, `ADMIN`, or `SUPERADMIN` roles.

### GET `/api/candidates/`
List candidates with advanced filtering and pagination.

**Query Parameters (all optional):**
| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (default: 1) |
| `limit` | int | Items per page, max 100 (default: 50) |
| `status` | string | Filter by candidate status |
| `search` | string | General search term |
| `name` | string | Filter by name |
| `branch` | string | Filter by academic branch |
| `college` | string | Filter by college |
| `cgpa_min` | float | Min CGPA (0-10) |
| `cgpa_max` | float | Max CGPA (0-10) |
| `passed_out_year` | int | Exact passed-out year |
| `language_choice` | string | Programming language preference |
| `has_resume` | bool | Has uploaded resume |
| `has_govt_id` | bool | Has uploaded govt ID |
| `created_after` | date | ISO date filter |
| `created_before` | date | ISO date filter |
| `email_verified` | bool | Email verification status |
| `phone` | string | Filter by phone |
| `email` | string | Filter by exact email |
| `cycle_id` | string | Filter by hiring cycle |
| `has_assessment` | bool | Has assessment records |
| `has_interview_feedback` | bool | Has interview feedback |
| `sort_by` | string | Sort column |
| `sort_order` | string | `asc` or `desc` |

**Response:**
```json
{
  "data": [ { ... } ],
  "pagination": { "page": 1, "limit": 50, "total": 100, "total_pages": 2 }
}
```

### GET `/api/candidates/me`
Get the authenticated candidate's own profile.

### GET `/api/candidates/{candidate_id}`
Get a single candidate by ID. Accessible by HR, ADMIN, SUPERADMIN, INTERVIEWER.

### PATCH `/api/candidates/{candidate_id}/status`
Update a candidate's pipeline status.

**Request:** `{ "status": "string" }` — accepts raw enum value or display status string.

**Response:** Updated CandidateRead object.

### POST `/api/candidates/bulk-upload/preview`
Preview CSV bulk upload without saving. Validates first 20 rows.

**Request:** `multipart/form-data` with `file` field (CSV).

**Response:** `BulkUploadPreview` with batch_id, counts, preview rows, and errors.

### POST `/api/candidates/bulk-upload`
Execute CSV bulk upload — saves valid records to the active hiring cycle.

**Request:** `multipart/form-data` with `file` field (CSV).

**CSV Format:** `email, name, college, branch, cgpa, passed_out_year, language_choice, phone`

**Response (201):**
```json
{
  "batch_id": "abc12345",
  "total_records": 50,
  "saved": 48,
  "errors": [ { "row": 12, "error": "Invalid CGPA" } ]
}
```

---

## 3. Assessments (`/api/assessment`)

### POST `/api/assessment/start`
Start a new assessment round for the current candidate.

**Request:**
```json
{ "round": "CODING" }
```

**Response (200):** `AssessmentRead` with id, questions, link_token, time_limit.

### GET `/api/assessment/active`
Get all active/in-progress assessments for the current candidate.

### GET `/api/assessment/{assessment_id}`
Get a single assessment by ID.

### POST `/api/assessment/{assessment_id}/complete`
Mark an assessment as completed and advance the candidate pipeline stage.

### POST `/api/assessment/submit-section`
Submit a section (MCQ or code) within an assessment.

**Request:**
```json
{
  "assessment_id": "uuid",
  "section": "MCQ",
  "content": {},
  "time_spent_seconds": 0
}
```

**Response:** Submission result.

---

## 4. Code Execution (`/api/code`)

Powered by **Piston** code execution engine.

### POST `/api/code/execute`
Run code with custom stdin — the "Run" button.

**Request:**
```json
{
  "language": "python",
  "code": "print('hello')",
  "stdin": ""
}
```

**Response:**
```json
{
  "status": "SUCCESS",
  "stdout": "hello\n",
  "stderr": "",
  "exit_code": 0,
  "execution_time_ms": 12.5
}
```

Supported languages: `python`, `java`, `cpp`, `javascript`

### POST `/api/code/evaluate`
Evaluate code against supplied test cases.

**Request:**
```json
{
  "language": "python",
  "code": "...",
  "test_cases": [
    { "input": "5", "expected_output": "25" }
  ]
}
```

**Response:**
```json
{
  "total_tests": 5,
  "passed_tests": 4,
  "failed_tests": 1,
  "score_percentage": 80.0,
  "test_results": [ ... ]
}
```

### POST `/api/code/evaluate-question/{question_id}`
Evaluate code against ALL test cases (public + private) for a stored question. Private test cases never leave the server.

---

## 5. Questions (`/api/questions`)

Questions are AI-generated and stored in-memory (not DB).

### POST `/api/questions/generate`
Generate a coding question via AI.

**Request:**
```json
{
  "topic": "arrays",
  "difficulty": "medium",
  "num_public_cases": 2,
  "num_private_cases": 3
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "difficulty": "medium",
  "boilerplate": "def solution():",
  "public_test_cases": [ ... ]
}
```

### GET `/api/questions/{question_id}/public`
Get public view of a question (no private test cases).

---

## 6. Proctoring (`/api/proctoring`)

### POST `/api/proctoring/event`
Record a proctoring event from the candidate's browser (tab switch, face detection, etc.).

**Request:**
```json
{
  "assessment_id": "uuid",
  "event_type": "TAB_SWITCH",
  "payload": {}
}
```

**Response (201):** Event record.

---

## 7. Interviews (`/api`)

Note: prefix is `/api`, so routes are at `/api/candidates/...`

### POST `/api/candidates/{candidate_id}/feedback`
Submit interviewer feedback for a candidate. Transitions candidate from `INTERVIEW_SCHEDULED` to `INTERVIEW_COMPLETED`.

**Roles:** INTERVIEWER, ADMIN, SUPERADMIN

**Request:**
```json
{
  "technicalScore": 7,
  "problemSolving": 8,
  "communicationScore": 6,
  "culturalFit": 9,
  "recommendation": "HIRE",
  "notes": "Strong candidate"
}
```

**Response (201):** `{ "id": "uuid", "message": "Feedback submitted" }`

### GET `/api/candidates/{candidate_id}/feedback`
Get all feedback entries for a candidate.

**Roles:** HR, ADMIN, SUPERADMIN

---

## 8. Selection (`/api/selection`)

### POST `/api/selection/candidates/{candidate_id}/select`
Select a candidate — moves them to `SELECTED` status. Requires status to be `INTERVIEW_COMPLETED` or `ROUND3_PASSED`.

**Roles:** HR, ADMIN, SUPERADMIN

### POST `/api/selection/candidates/bulk-select`
Bulk-select candidates.

**Request:** `[ { "candidate_id": "uuid" }, ... ]`

### POST `/api/selection/candidates/{candidate_id}/reject`
Reject a candidate — moves to `FINAL_REJECTED` status.

---

## 9. Analytics (`/api/analytics`)

### GET `/api/analytics/funnel`
Get hiring pipeline funnel data with extensive filtering.

**Query Parameters:** Same filter set as candidates list (branch, college, cgpa, dates, etc.) plus:
| Param | Type | Description |
|-------|------|-------------|
| `target_statuses` | string | Comma-separated list to filter funnel stages |
| `status` | string | Filter by candidate status |

### GET `/api/analytics/dashboard`
Get aggregate dashboard metrics.

**Roles:** HR, ADMIN, SUPERADMIN

---

## 10. Admin (`/api/admin`)

### GET `/api/admin/users`
List all platform users with pagination.

**Roles:** SUPERADMIN, ADMIN

### GET `/api/admin/organizations`
**Deprecated** — multi-tenancy removed. Returns empty list.

### POST `/api/admin/organizations`
**Deprecated** — raises error.

### PATCH `/api/admin/organizations/{org_id}`
**Deprecated** — no-op.

---

## 11. Hiring Cycles (`/api/hiring-cycles`)

### GET `/api/hiring-cycles/`
List all hiring cycles ordered by created_at descending.

**Roles:** HR, ADMIN, SUPERADMIN

### POST `/api/hiring-cycles/`
Create a new hiring cycle.

**Roles:** ADMIN, SUPERADMIN

**Request:**
```json
{
  "name": "Summer 2026",
  "start_date": "2026-06-01",
  "end_date": "2026-08-31",
  "eligibility_config": { "min_cgpa": 6.0, "allowed_branches": ["CSE", "ECE"] },
  "assessment_config": {},
  "proctoring_config": {}
}
```

### PATCH `/api/hiring-cycles/{cycle_id}`
Update a hiring cycle's fields.

**Roles:** ADMIN, SUPERADMIN

---

## 12. Screening (`/api/screening`)

### GET `/api/screening/pipeline-stats`
Get pipeline statistics for the dashboard — status counts, aggregates, average CGPA.

### POST `/api/screening/run`
Run screening against the active hiring cycle's eligibility config. Evaluates all `APPLIED` candidates and transitions them to `ROUND1_PASSED` or `ROUND1_REJECTED` with rejection reasons.

**Response:**
```json
{
  "screened": 100,
  "passed": 65,
  "rejected": 35,
  "min_cgpa": 6.0,
  "allowed_branches": ["CSE", "ECE", "IT", "EEE"],
  "cycle_name": "Summer 2026",
  "details": [ { "name": "...", "email": "...", "result": "ELIGIBLE", "reasons": [] } ]
}
```

---

## 13. Health

### GET `/health`
Simple health check — does not require auth.

**Response:** `{ "status": "ok" }`

---

## 14. Unregistered Routes (not wired in `main.py`)

These route files exist in `backend/app/features/` but are **NOT currently imported or registered** in `main.py`:

### `/api/audit` — Audit Logs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/audit/logs` | List audit logs (paginated, filterable by entity_type) |

**Roles:** ADMIN, SUPERADMIN

### `/api/jobs` — Job Management
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/jobs/` | Create a job posting |
| GET | `/api/jobs/` | List all jobs (optional `status` filter) |
| GET | `/api/jobs/{job_id}` | Get a single job |
| PATCH | `/api/jobs/{job_id}` | Update a job |
| DELETE | `/api/jobs/{job_id}` | Delete a job |

### `/api/phase2` — Phase 2 Assessment
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/phase2/start/{applicant_id}` | HR triggers Phase 2 for a candidate |
| GET | `/api/phase2/my-assessment` | Candidate gets assigned questions |
| POST | `/api/phase2/submit` | Candidate submits code for evaluation |
| GET | `/api/phase2/results/{applicant_id}` | HR views candidate scores |

### `/api/superadmin` — SuperAdmin Platform Management
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/superadmin/organizations` | Platform overview stats |
| GET | `/api/superadmin/users` | List all users (paginated) |
| PATCH | `/api/superadmin/users/{user_id}/role` | Update a user's role |

---

## Authentication & Authorization

### Token Flow
1. **Login/Register** → returns `access_token` (JWT, short-lived) + sets `kf_refresh_token` (httpOnly cookie, 7 days)
2. **All API calls** → include `Authorization: Bearer <access_token>` header
3. **Token refresh** → `POST /api/auth/refresh` reads the cookie automatically

### Roles (hierarchical)
| Role | Level |
|------|-------|
| `CANDIDATE` | Lowest — can only access own profile and assessments |
| `INTERVIEWER` | Can submit feedback |
| `HR` | Manages candidates, pipeline, analytics |
| `ADMIN` | Full platform management |
| `SUPERADMIN` | God-mode — user management, role changes |

### Frontend Token Storage
- `localStorage.kf_token` — access token
- `localStorage.kf_user` — user profile JSON
- Auto-injected into every API request by the central `api` client

---

## Error Handling

All errors return consistent JSON:
```json
{
  "detail": "Human-readable error message"
}
```

Common HTTP status codes:
| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request / validation error |
| 401 | Unauthenticated |
| 403 | Forbidden (wrong role) |
| 404 | Resource not found |
| 422 | Unprocessable entity (status transition, validation) |
| 500 | Server error |
| 502 | Upstream service failed (AI generation, code sandbox) |

---

## Data Models (Key Request/Response Schemas)

### Candidate (CandidateRead)
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| name | string | Full name |
| email | string | Email address |
| phone | string? | Phone number |
| college | string? | College name |
| branch | string? | Academic branch |
| cgpa | float | CGPA (0-10) |
| passed_out_year | int | Graduation year |
| language_choice | string | Preferred language |
| status | string | Pipeline status |
| resume_url | string? | Resume file path |
| govt_id_url | string? | Govt ID file path |
| cycle_id | string? | Hiring cycle ID |
| custom_fields | dict | Flexible metadata |
| created_at | datetime | Timestamp |

### HiringCycle
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| name | string | Cycle name |
| start_date | date | Start date |
| end_date | date | End date |
| status | string | ACTIVE, INACTIVE, CLOSED |
| eligibility_config | json | CGPA, branches, years |
| assessment_config | json | Assessment settings |
| proctoring_config | json | Proctoring settings |
| created_by | uuid | Creator user ID |
| created_at | datetime | Timestamp |

### Assessment
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| candidate_id | uuid | Candidate reference |
| round | string | CODING, MCQ |
| status | string | NOT_STARTED, IN_PROGRESS, COMPLETED |
| questions_json | dict | Question data |
| link_token | string | Secure access token |
| link_expiry | datetime | Token expiry |
| time_limit | int | Minutes allowed |

### User
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| email | string | Unique email |
| name | string | Full name |
| role | string | Role enum value |
| status | string | ACTIVE, INACTIVE |
| password_hash | string | BCrypt hash |
| created_at | datetime | Timestamp |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite+aiosqlite:///./knowledge_factory.db` | DB connection string |
| `CORS_ORIGINS` | No | `http://localhost:5173,http://localhost:3000` | Allowed origins |
| `JWT_SECRET_KEY` | Yes | — | Secret for JWT signing |
| `AI_API_KEY` | No | — | API key for AI question generation |
| `SANDBOX_URL` | No | — | Piston code sandbox URL |
| `DEBUG` | No | `true` | Enables Swagger docs, verbose errors |
| `APP_NAME` | No | `Knowledge Factory` | App title |
| `APP_VERSION` | No | `1.0.0` | App version |

---

## Running the Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Interactive API docs at `http://localhost:8000/docs`
