# API Route Documentation

*(This is a structural overview. For exhaustive details on all endpoints, refer to `API_DOCUMENTATION.md` and `API_AUDIT_REPORT.md`.)*

## Module Groupings

### 1. Authentication (`/api/auth/*`)
Handles login, registration, password resets, and token refreshing via HTTPOnly cookies.

### 2. Candidates (`/api/candidates/*`)
Manages the candidate lifecycle, bulk uploads, profile retrieval, status updates, and resume uploading/parsing.

### 3. Assessments (`/api/assessment/*`)
Handles the initialization, progression, submission, and completion of automated testing rounds.

### 4. Code Execution (`/api/code/*`)
Integrates with the Piston engine to execute and evaluate code snippets against test cases.

### 5. Proctoring (`/api/proctoring/*`)
Manages WebSocket session creation, event logging, risk calculation, and manual/automatic test termination.

### 6. Interviews (`/api/candidates/{id}/feedback`)
Allows interviewers to submit and review human feedback on a candidate.

### 7. Selection (`/api/selection/*`)
Provides candidate ranking lists and endpoints for finalizing HR hiring decisions.

### 8. Analytics (`/api/analytics/*`)
Provides aggregated data for the dashboard and the stage-by-stage hiring funnel.

### 9. Admin (`/api/admin/*`)
User management (creating HR/Interviewers) and system-wide audit logging.

### 10. Hiring Cycles (`/api/hiring-cycles/*`)
CRUD operations for the hiring campaigns that group candidates and define configuration thresholds.

### 11. Screening (`/api/screening/*`)
Triggers the automatic processing of candidates from APPLIED to ROUND1_PASSED based on eligibility configs.
