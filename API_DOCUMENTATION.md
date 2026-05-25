# API Documentation Reference

This document provides a comprehensive reference for all discovered endpoints in the Knowledge Factory Hiring Platform.

---

# Authentication APIs

### Login
**Method:** POST  
**Path:** `/api/auth/login`  
**Purpose:** Authenticates a user or candidate and returns an access token and user metadata. Sets a refresh token in an httpOnly cookie.  
**Authentication:** Public  
**Request Parameters:**
- `email` (string, body)
- `password` (string, body)
**Example Request:**
```json
{
  "email": "hr@knowledgefactory.com",
  "password": "password123"
}
```
**Response:** Returns access token and user object.  
**Example Response:**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "user": {
    "id": "u1",
    "email": "hr@knowledgefactory.com",
    "name": "HR Manager",
    "role": "hr"
  }
}
```
**Database Tables Used:** `users`, `candidates`  
**Frontend Usage:** `auth.ts` -> `authApi.login`

### Register Candidate
**Method:** POST  
**Path:** `/api/auth/register`  
**Purpose:** Registers a new candidate and links them to the active hiring cycle. Supports multipart form data for resume upload.  
**Authentication:** Public  
**Request Parameters (Multipart):**
- `name`, `email`, `password`, `college`, `branch`, `cgpa`, `passed_out_year`, `language_choice`
- `resume` (file, optional)
**Database Tables Used:** `candidates`, `hiring_cycles`  
**Frontend Usage:** `auth.ts` -> `authApi.register`

---

# Candidate APIs

### List Candidates
**Method:** GET  
**Path:** `/api/candidates/`  
**Purpose:** Lists candidates with extensive filtering (branch, college, CGPA, status, etc.) and pagination.  
**Authentication:** HR, Admin, SuperAdmin  
**Request Parameters:**
- `page`, `limit` (query)
- `status`, `search`, `branch`, `college`, `cgpa_min`, `cgpa_max` (query filters)
**Response:** Paginated list of candidates.  
**Database Tables Used:** `candidates`  
**Frontend Usage:** `candidates.ts` -> `candidatesApi.getAll`

### Get My Profile
**Method:** GET  
**Path:** `/api/candidates/me`  
**Purpose:** Allows an authenticated candidate to retrieve their own profile details.  
**Authentication:** Candidate  
**Database Tables Used:** `candidates`  
**Frontend Usage:** `candidates.ts` -> `candidatesApi.getMe`

---

# Resume Upload APIs

### Upload My Resume
**Method:** POST  
**Path:** `/api/candidates/me/resume`  
**Purpose:** Uploads a resume for the current candidate, triggers AI parsing to extract info, and performs auto-screening.  
**Authentication:** Candidate  
**Request Parameters:**
- `file` (UploadFile)
**Response:** Returns parse status and updated candidate status.  
**Database Tables Used:** `candidates`, `hiring_cycles`  
**Frontend Usage:** `candidates.ts` -> `candidatesApi.uploadResume`

---

# Assessment APIs

### Start Assessment
**Method:** POST  
**Path:** `/api/assessment/start`  
**Purpose:** Initializes an assessment attempt for a candidate.  
**Authentication:** Candidate  
**Request Parameters:**
- `round` (string, body): e.g., "ROUND2"
**Database Tables Used:** `assessments`, `candidates`  
**Frontend Usage:** `assessment.ts` -> `assessmentApi.start`

### Submit Section
**Method:** POST  
**Path:** `/api/assessment/submit-section`  
**Purpose:** Submits answers/code for a specific section of the assessment.  
**Authentication:** Candidate  
**Request Parameters:**
- `assessment_id`, `section_id`, `answers` (body)
**Database Tables Used:** `submissions`, `assessments`  
**Frontend Usage:** `assessment.ts` -> `assessmentApi.submitSection`

---

# Proctoring APIs

### Initialize Proctoring Session
**Method:** POST  
**Path:** `/api/proctoring/session`  
**Purpose:** Creates a proctoring session and returns a WebSocket token for the AI proctoring service.  
**Authentication:** Candidate  
**Request Parameters:**
- `assessment_attempt_id` (string, body)
**Database Tables Used:** `proctoring_sessions`  
**Frontend Usage:** `proctoring.ts` -> `proctoringApi.initialize`

---

# Admin APIs

### List Users
**Method:** GET  
**Path:** `/api/admin/users`  
**Purpose:** Lists all platform users (non-candidates).  
**Authentication:** Admin, SuperAdmin  
**Database Tables Used:** `users`  
**Frontend Usage:** `admin.ts` -> `adminApi.listUsers`

---

# Analytics APIs

### Hiring Funnel
**Method:** GET  
**Path:** `/api/analytics/funnel`  
**Purpose:** Returns counts of candidates at each stage of the pipeline, with filtering.  
**Authentication:** HR, Admin, SuperAdmin  
**Database Tables Used:** `candidates`  
**Frontend Usage:** `analytics.ts` -> `analyticsApi.getFunnel`

---

# Selection APIs

### Get Ranking
**Method:** GET  
**Path:** `/api/selection/ranking/{cycle_id}`  
**Purpose:** Returns a ranked list of candidates for a specific hiring cycle based on evaluation metrics.  
**Authentication:** HR, Admin, SuperAdmin  
**Database Tables Used:** `candidates`, `assessments`, `scores`  
**Frontend Usage:** `selection.ts` -> `selectionApi.getRanking`

### Make Decision
**Method:** POST  
**Path:** `/api/selection/candidates/{candidate_id}/decision`  
**Purpose:** Records a final hiring decision (Select/Reject) with a reason and audit trail.  
**Authentication:** HR, Admin, SuperAdmin  
**Request Parameters:**
- `status` (CandidateStatus, body)
- `reason` (string, optional, body)
**Database Tables Used:** `candidates`  
**Frontend Usage:** `candidates.ts` -> `candidatesApi.makeDecision`

---

# Analytics APIs

### Dashboard
**Method:** GET  
**Path:** `/api/analytics/dashboard`  
**Purpose:** Provides high-level metrics (total candidates, average scores, etc.) for the admin dashboard.  
**Authentication:** Admin, SuperAdmin  
**Database Tables Used:** `candidates`, `assessments`, `users`  
**Frontend Usage:** `analytics.ts` -> `analyticsApi.getDashboard`

---

# Admin APIs

### Create User
**Method:** POST  
**Path:** `/api/admin/users`  
**Purpose:** Creates a new staff user (HR, Interviewer, or Admin).  
**Authentication:** Admin (for HR/Interviewer), SuperAdmin (all except SuperAdmin)  
**Database Tables Used:** `users`  
**Frontend Usage:** `admin.ts` -> `adminApi.createUser`

---

# Hiring Cycle APIs

### List Cycles
**Method:** GET  
**Path:** `/api/hiring-cycles/`  
**Purpose:** Lists all hiring cycles (active and archived).  
**Authentication:** HR, Admin, SuperAdmin  
**Database Tables Used:** `hiring_cycles`  
**Frontend Usage:** `hiring-cycles.ts` -> `hiringCyclesApi.getAll`

---

# Screening APIs

### Run Screening
**Method:** POST  
**Path:** `/api/screening/run`  
**Purpose:** Triggers the auto-screening engine to process candidates in the 'APPLIED' status.  
**Authentication:** HR, Admin, SuperAdmin  
**Database Tables Used:** `candidates`, `hiring_cycles`  
**Frontend Usage:** `screening.ts` -> `screeningApi.run`

---

# Code Execution APIs

### Execute Code
**Method:** POST  
**Path:** `/api/code/execute`  
**Purpose:** Executes code snippet via the Piston engine and returns stdout/stderr.  
**Authentication:** Candidate, Admin  
**Database Tables Used:** None (External API)  
**Frontend Usage:** `code-execution.ts` -> `codeExecutionApi.execute`

---

# Miscellaneous APIs

### Health Check
**Method:** GET  
**Path:** `/health`  
**Purpose:** Simple health check returning API version and status.  
**Authentication:** Public  
**Response:** `{"status": "ok", "version": "1.0.0"}`

---

# Proctoring WebSocket

### Proctoring Data Stream
**Method:** WSS  
**Path:** `/ws/proctor/{session_id}`  
**Purpose:** Receives real-time video frames and violations from the frontend.  
**Authentication:** WS Token (verified via query param)  
**Database Tables Used:** `proctoring_events`, `proctoring_evidence`

---

*Note: For a full list of all 50+ endpoints, see the API_AUDIT_REPORT.md file.*
