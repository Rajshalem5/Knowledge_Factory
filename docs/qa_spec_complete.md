# Knowledge Factory — Complete QA Automation Spec

## Overview
Autonomous black-box E2E testing for the KF intern recruitment platform.
Runs every 2h via cron with Hermes agent. Uses agent-browser CLI ONLY.

## Environment Variables (from /backend/.env and /app/.env)
- NGROK_URL: from /mnt/hermes-shared/projects/Knowledge_Factory/ngrok_url.txt
- SUPER_ADMIN_EMAIL=admin@knowledgefactory.com  SUPER_ADMIN_PASS=Admin123!
- HR_EMAIL=hr@knowledgefactory.com  HR_PASS=HR123!
- INTERVIEWER_EMAIL=interviewer@knowledgefactory.com  INTERVIEWER_PASS=Interview123!
- CANDIDATE_EMAIL=candidate1@student.edu  CANDIDATE_PASS=Candidate123!
- CANDIDATE2_EMAIL=candidate2@student.edu  CANDIDATE2_PASS=Candidate123!
- PISTON_URL from backend .env
- KF_BACKEND_URL = http://localhost:8000 (or 8002)
- KF_PROJECT_PATH = /mnt/hermes-shared/projects/Knowledge_Factory

## Known .env Flags (every run — CONFIG WARNINGS)
- VITE_API_URL empty — frontend may not reach backend
- SENDGRID_API_KEY empty — all email flows silently fail
- DATABASE_URL duplicate — SQLite wins
- DEBUG=true — /docs and /redoc publicly accessible

## Pre-Flight Checks (Before Every Main Run)

### 1. ngrok
  curl -s -o /dev/null -w "%{http_code}" $NGROK_URL/health
  Expect 200 with {"status": "ok"}
  If down — skip run, Telegram alert, retry once after 60s

### 2. Backend Health
  GET http://localhost:8000/health (or 8002) — expect {"status": "ok"}
  If down — attempt restart via `runkf` skill, report 🔴 CRITICAL

### 3. Frontend Build
  agent-browser open $NGROK_URL → assert no 404s, no build errors in console

### 4. Database
  SQLite at /mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db
  Check all 11 tables exist: ai_generation_logs, email_logs, users, audit_logs, hiring_cycles, candidates, assessments, interview_feedback, scores, proctoring_records, submissions

### 5. Test User Login (all 5 roles)
  Login each role before main run. If any fails → BLOCKED role

### 6. Piston API
  POST $PISTON_URL/execute — hello-world test. If down — skip code exec tests

## Auth State Files (for speed)
Path: /opt/hermes_shared_memory/projects/Knowledge_Factory/auth/{role}.json
Roles: superadmin, admin, hr, interviewer, candidate
If login test fails — delete saved state, re-login fresh, re-save.

## agent-browser Workflow
1. agent-browser --session {role} open $NGROK_URL
2. agent-browser --session {role} snapshot -i --json
3. Interact via refs (@e1, @e2...) from snapshot only
4. Re-snapshot after every page change
5. agent-browser --session {role} network requests --status 4xx,5xx
6. agent-browser --session {role} console --json
7. agent-browser --session {role} errors

## Parallel Role Sessions
Run all 5 concurrently: superadmin, admin, hr, interviewer, candidate

## Layers (Run in Order)

### LAYER 1: Server & Infrastructure
- Backend /health → {"status": "ok"}
- /docs accessible (DEBUG=true — tag CONFIG WARNING)
- CORS headers on /api/*
- Frontend assets: no 404s, no build errors
- Known .env flags

### LAYER 2: Auth & RBAC
- Login all 5 roles
- Wrong password → 401
- Register new candidate → 201
- Verify-OTP flow
- Forgot password → 200 (email won't send)
- Refresh token → new token
- Logout → session cleared
- Expired/tampered JWT → 401
- Token in localStorage.kf_token after login
- Rate limit: 5 login attempts/15min, 20 code exec/min
- RBAC: Candidate → /api/candidates → 403; Interviewer → /superadmin redirect
- ProtectedRoute: portal→candidate, dashboard→hr/admin/superadmin, etc.

### LAYER 3: Candidate Pipeline
- Register QA candidate (qa_test_{run_id}@test.com)
- Login as HR → verify status APPLIED
- POST /api/screening/run → 200
- Verify pipeline-stats updated
- Start assessment → 200, status ROUND2_IN_PROGRESS
- Code execute → output returned (if Piston healthy)
- Code evaluate → pass/fail correct
- Tab switch → proctoring event fired
- Complete assessment → ROUND2_PASSED
- Interview feedback → INTERVIEW_COMPLETED → SELECTED
- Final selection → SELECTED/REJECTED
- Clean up: delete qa_test_* candidates

### LAYER 4: HR Dashboard
- GET /api/candidates — paginated, sorted, filtered
- CSV download
- Bulk upload test
- Candidate detail page
- Known gaps: no assessment UI, no bulk actions

### LAYER 5: Interviewer Panel
- Only assigned candidates visible
- Submit feedback
- Status persists

### LAYER 6: Analytics
- /analytics page loads
- Check for "Cannot read properties of undefined" errors
- GET /api/analytics/dashboard — real data (status_breakdown), mocks for passRatePerRound/collegeBreakdown/branchPerformance/proctoringViolations
- GET /api/analytics/funnel — real DB counts
- GET /api/screening/pipeline-stats — real counts

### LAYER 7: Code Execution
- Skip if Piston down
- POST /api/code/execute — python print('hello') → output "hello", <10s
- POST /api/code/evaluate — known code + test cases
- Timeout on infinite loops
- Test Python + JS

### LAYER 8: Proctoring
- POST /api/proctoring/event → 200
- Event stored in proctoring_records
- WebSocket proctoring = Phase 2 stub — skip

### LAYER 9: Admin & SuperAdmin
- GET /api/admin/users
- GET /api/superadmin/organizations
- GET /api/superadmin/users
- PATCH /api/superadmin/users/{id}/role
- GET /api/audit/logs
- Hiring Cycles CRUD

### LAYER 10: Error Handling
- /api/nonexistent-route → JSON error not HTML
- Invalid data → 422 with clear message
- Nonexistent ID → 404 JSON
- Duplicate email → proper error
- Special chars → saved correctly
- Empty states → renders not crashes
- Network error → error message shown

### LAYER 11: Security Probes
- XSS: register with <script>alert('xss')</script> — rendered as text
- SQLi: login with "' OR 1=1 --" → 422/401
- File upload: .exe as resume → rejected
- JWT tampering → 401
- Unprotected endpoints scan (no auth header)
- Cross-role access probe

### LAYER 12: Frontend UX
- Role-specific sidebar links
- No blank pages
- Modals open/close cleanly
- Toast notifications
- Loading spinners
- 404 page
- Mobile viewport (390x844) — horizontal scroll, no overflow

## Enhancements

### ENH 1: Pytest Suite
cd $KF_PROJECT_PATH/backend && pytest tests/ -q --tb=short 2>&1
Report X passed / Y failed / Z errors

### ENH 2: Response-Time Baseline
Check endpoints with Python requests timing
Thresholds: <500ms FAST, 500-1000 OK, 1000-3000 MEDIUM, 3000-5000 HIGH, >5000 CRITICAL
Store/compare vs /opt/hermes_shared_memory/projects/Knowledge_Factory/perf_baseline.json

### ENH 3: Dependency Security Audit (every 6h)
pip-audit -r requirements.txt + npm audit
Classify CRITICAL/HIGH/MODERATE/LOW CVEs
Report new vs previous audit

### ENH 4: DB Integrity
PRAGMA integrity_check
Row counts per table
Missing indexes
FK violations
Store counts, alert on drops

### ENH 5: Frontend JS Console
Per role after login: console --json, errors
Classify console.error, unhandled rejections, React runtime errors
Blank page detection
Broken images detection

### ENH 6: Unprotected Endpoint Scan
Static code analysis: grep for routes missing auth dependency
Runtime probe without JWT
Cross-role access probe

## Known Permanent Issues (tag ⚠️ never count as failures)
1. SENDGRID_API_KEY empty — emails fail
2. VITE_API_URL empty
3. DATABASE_URL duplicate — SQLite active
4. passRatePerRound mock [75,60,45]
5. collegeBreakdown/branchPerformance/proctoringViolations return []
6. WebSocket proctoring = stub
7. WebSocket dashboard = stub
8. No HR UI to assign assessments
9. No automatic status transitions beyond R1
10. No candidate notifications
11. No bulk actions
12. DEBUG=true — /docs public
13. /api/screening/run — NO AUTH
14. /api/screening/pipeline-stats — NO AUTH
15. Candidates may auto-move to SELECTED
16. No assessment results view for HR
17. Forgot-password email = TODO stub

## Telegram Report Format
See README in project for the exact format. Key sections:
- Summary (pass/fail/critical counts)
- Role Status (✅/❌/🚫 BLOCKED)
- Systems status
- Config warnings
- Known issues triggered
- Failures with screenshots
- Performance report
- Security scan
- Pytest results
- Fixed this run
- All passing

## Behavior Rules
- agent-browser only — no Playwright/Selenium
- Always snapshot before interacting
- Re-snapshot after every page change
- Never skip sections
- Screenshot every failure with --annotate
- Known issues → ⚠️ never counted
- Clean up: agent-browser close --all after run
- Delete qa_test_* candidates after run
- Never touch production data
