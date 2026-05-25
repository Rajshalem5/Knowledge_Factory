# Database Documentation

The platform uses SQLAlchemy 2.0 ORM. The default local development database is SQLite, while production utilizes PostgreSQL.

## Entity Relationship Overview
*   A `HiringCycle` has many `Candidates`.
*   A `Candidate` has many `Assessments`, `Scores`, and `InterviewFeedbacks`.
*   An `Assessment` has many `Submissions` and one `ProctoringSession`.
*   A `ProctoringSession` has many `ProctoringEvents`, `ProctoringEvidence`, and `RiskSnapshots`.
*   A `User` (HR/Admin/Interviewer) creates `HiringCycles`, evaluates `Candidates`, and is tracked via `AuditLogs`.

---

## Table Definitions

### 1. `users`
System operators (HR, Admin, Interviewer, SuperAdmin).
*   `id` (String 36, PK)
*   `email` (String 255, Unique)
*   `password_hash` (String 255)
*   `name` (String 255)
*   `role` (Enum: HR, ADMIN, SUPER_ADMIN, INTERVIEWER)
*   `status` (String 50)
*   `created_at` (DateTime)

### 2. `hiring_cycles`
Defines the parameters and timeframe for a hiring drive.
*   `id` (String 36, PK)
*   `name` (String 255)
*   `start_date` (Date)
*   `end_date` (Date)
*   `status` (Enum: DRAFT, ACTIVE, COMPLETED)
*   `eligibility_config` (JSON)
*   `assessment_config` (JSON)
*   `proctoring_config` (JSON)
*   `created_by` (String 36, FK -> users.id)
*   `created_at` (DateTime)

### 3. `candidates`
Applicants applying for a job within a hiring cycle.
*   `id` (String 36, PK)
*   `cycle_id` (String 36, FK -> hiring_cycles.id)
*   `email` (String 255, Unique)
*   `phone` (String 20)
*   `name` (String 255)
*   `college` (String 255)
*   `branch` (String 50)
*   `cgpa` (Numeric 4,2)
*   `passed_out_year` (Integer)
*   `resume_url` (String 500)
*   `language_choice` (String 30)
*   `status` (Enum: APPLIED, ROUND1_PASSED, SELECTED, etc.)
*   `composite_score` (Numeric 5,2)
*   `recommendation` (String 30)
*   `created_at` (DateTime)
*   `updated_at` (DateTime)

### 4. `assessments`
A specific test attempt by a candidate.
*   `id` (String 36, PK)
*   `candidate_id` (String 36, FK -> candidates.id)
*   `round` (Enum: ROUND2, ROUND3)
*   `questions_json` (JSON)
*   `status` (Enum: NOT_STARTED, IN_PROGRESS, COMPLETED, TERMINATED)
*   `started_at` (DateTime)
*   `ended_at` (DateTime)
*   `time_limit` (Integer)

### 5. `submissions`
Code or answers submitted during an assessment.
*   `id` (String 36, PK)
*   `assessment_id` (String 36, FK -> assessments.id)
*   `section` (Enum: MCQ, CODING)
*   `payload_json` (JSON)
*   `time_spent_seconds` (Integer)
*   `submitted_at` (DateTime)

### 6. `scores`
Evaluated results of an assessment.
*   `id` (String 36, PK)
*   `candidate_id` (String 36, FK -> candidates.id)
*   `round` (Enum)
*   `correctness` (Integer)
*   `quality` (Integer)
*   `mcq_total` (Integer)
*   `weighted_total` (Numeric 5,2)
*   `verdict` (Enum: PASS, FAIL, BORDERLINE)

### 7. `proctoring_sessions`
Live monitoring state for an assessment.
*   `id` (String 36, PK)
*   `assessment_attempt_id` (String 36, FK -> assessments.id)
*   `user_id` (String 36, FK -> users.id)
*   `status` (String 20: ACTIVE, TERMINATED)
*   `final_risk_score` (Float)
*   `total_violations` (Integer)

### 8. `proctoring_events`
Specific violations or logs during a session.
*   `id` (String 36, PK)
*   `session_id` (String 36, FK -> proctoring_sessions.id)
*   `event_type` (String 50: TAB_SWITCH, PHONE_DETECTED)
*   `severity` (String 20: LOW, HIGH)
*   `risk_score` (Float)
*   `metadata` (JSON)

### 9. `proctoring_evidence`
Media (screenshots/audio) captured during an event.
*   `id` (String 36, PK)
*   `session_id` (String 36, FK -> proctoring_sessions.id)
*   `event_type` (String 50)
*   `screenshot_url` (String 500)
*   `transcript` (Text)

### 10. `interview_feedback`
Human review data.
*   `id` (String 36, PK)
*   `candidate_id` (String 36, FK -> candidates.id)
*   `interviewer_id` (String 36, FK -> users.id)
*   `technical` (Integer)
*   `communication` (Integer)
*   `recommendation` (String: HIRE, REJECT, HOLD)
*   `comments` (Text)
