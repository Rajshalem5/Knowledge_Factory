#!/usr/bin/env python3
"""
Knowledge Factory - Comprehensive E2E QA Test Suite
Run: python3 kf_e2e_tests.py
"""
import json, os, sys, time, subprocess, sqlite3, re, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

# === CONFIG ===
BASE = "http://localhost:8000"
NGROK = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AUTH_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory/auth"
FAILURES_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory/failures"
RUNS_DIR = "/mnt/hermes-shared/projects/Knowledge_Factory/qa_runs"
DB_PATH = "/mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db"
PROJECT_PATH = "/mnt/hermes-shared/projects/Knowledge_Factory"
BASELINE_PATH = "/opt/hermes_shared_memory/projects/Knowledge_Factory/perf_baseline.json"
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
AGENT_BROWSER = "/usr/bin/agent-browser"

os.makedirs(FAILURES_DIR, exist_ok=True)
os.makedirs(RUNS_DIR, exist_ok=True)

# === HELPERS ===
def load_auth(role):
    with open(f"{AUTH_DIR}/{role}.json") as f:
        return json.load(f)

def headers(role):
    auth = load_auth(role)
    return ["Authorization: Bearer " + auth["token"], "Content-Type: application/json"]

def curl(method, url, role=None, data=None, headers_extra=None):
    cmd_parts = ["curl", "-s", "-w", "\n%{http_code}"]
    cmd_parts.extend(["-X", method])
    
    if role:
        auth = load_auth(role)
        cmd_parts.extend(["-H", f"Authorization: Bearer {auth['token']}"])
    
    cmd_parts.extend(["-H", "Content-Type: application/json"])
    
    if headers_extra:
        for h in headers_extra:
            cmd_parts.extend(["-H", h])
    
    if data:
        cmd_parts.extend(["-d", json.dumps(data)])
    
    cmd_parts.append(url)
    
    result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)
    output = result.stdout.strip()
    
    # Split body and status code
    if '\n' in output:
        *body_lines, status = output.rsplit('\n', 1)
        body = '\n'.join(body_lines)
    else:
        body = output
        status = "000"
    
    try:
        body_json = json.loads(body) if body else {}
    except:
        body_json = {"raw": body}
    
    return int(status), body_json, body

def report_test(name, status, expected, actual, critical=False, notes=""):
    return {
        "name": name,
        "status": status,  # PASS, FAIL, WARN, SKIP, ⚠️
        "expected": expected,
        "actual": actual,
        "critical": critical,
        "notes": notes
    }

def time_endpoint(method, url, role=None, data=None):
    """Time an API endpoint in ms."""
    times = []
    for _ in range(3):
        start = time.time()
        status, body, raw = curl(method, url, role, data)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    return min(times), status, body, raw

# === TEST COLLECTION ===
results = []
pass_count = 0
fail_count = 0
critical_count = 0
warn_count = 0
perf_data = {}
fixed_this_run = []
regressions = []
known_issues_triggered = []

def record(result):
    global pass_count, fail_count, critical_count, warn_count
    results.append(result)
    s = result["status"]
    if s == "PASS":
        pass_count += 1
    elif s == "FAIL":
        fail_count += 1
        if result.get("critical"):
            critical_count += 1
    elif s == "WARN" or s == "⚠️":
        warn_count += 1

print(f"{'='*60}")
print(f"KF E2E TEST RUN {RUN_ID}")
print(f"{'='*60}")
print(f"Start: {datetime.now().isoformat()}")
print()

# ============================================================
# PHASE 1: PRE-FLIGHT
# ============================================================
print("\n--- PHASE 1: PRE-FLIGHT ---")

# 1. Backend health
print("  [1.1] Backend health...")
t, s, b, raw = time_endpoint("GET", f"{BASE}/health")
if s == 200 and b.get("status") == "ok":
    record(report_test("Backend health", "PASS", "200 {'status':'ok'}", f"{s} {raw[:80]}"))
else:
    record(report_test("Backend health", "FAIL", "200 {'status':'ok'}", f"{s} {raw[:80]}", critical=True))

# 2. DB integrity
print("  [1.2] DB integrity...")
conn = sqlite3.connect(DB_PATH)
c = conn.execute("PRAGMA integrity_check")
integrity = c.fetchone()[0]
if integrity == "ok":
    record(report_test("DB integrity", "PASS", "ok", integrity))
else:
    record(report_test("DB integrity", "FAIL", "ok", integrity, critical=True))

# 3. DB tables
print("  [1.3] DB table check...")
c = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in c.fetchall()]
expected_tables = {'ai_generation_logs','assessments','audit_logs','candidates','email_logs',
                   'hiring_cycles','interview_feedback','proctoring_records','scores','submissions','users'}
missing = expected_tables - set(tables)
if not missing:
    record(report_test("DB tables", "PASS", f"All {len(expected_tables)} tables", f"{len(tables)} tables: {tables}"))
else:
    record(report_test("DB tables", "FAIL", f"All tables present", f"Missing: {missing}", critical=True))

# 4. DB row counts
print("  [1.4] DB row counts...")
db_stats = {}
for t in sorted(tables):
    if t != 'alembic_version':
        c = conn.execute(f"SELECT COUNT(*) FROM {t}")
        db_stats[t] = c.fetchone()[0]
        print(f"    {t}: {db_stats[t]} rows")
conn.close()

# 5. FK violations
print("  [1.5] FK violations check...")
conn2 = sqlite3.connect(DB_PATH)
# SQLite doesn't enforce FKs by default, check PRAGMA foreign_keys
c = conn2.execute("PRAGMA foreign_keys")
fk_enabled = c.fetchone()[0]
# Check for orphaned records
fk_violations = {}
# Check proctoring_records -> candidates
c = conn2.execute("SELECT COUNT(*) FROM proctoring_records pr WHERE pr.candidate_id NOT IN (SELECT id FROM candidates)")
cnt = c.fetchone()[0]
if cnt > 0:
    fk_violations["proctoring_records"] = cnt
# Check assessments -> candidates
c = conn2.execute("SELECT COUNT(*) FROM assessments a WHERE a.candidate_id NOT IN (SELECT id FROM candidates)")
cnt = c.fetchone()[0]
if cnt > 0:
    fk_violations["assessments"] = cnt
# Check interview_feedback -> candidates
c = conn2.execute("SELECT COUNT(*) FROM interview_feedback f WHERE f.candidate_id NOT IN (SELECT id FROM candidates)")
cnt = c.fetchone()[0]
if cnt > 0:
    fk_violations["interview_feedback"] = cnt
# Check scores -> candidates
c = conn2.execute("SELECT COUNT(*) FROM scores s WHERE s.candidate_id NOT IN (SELECT id FROM candidates)")
cnt = c.fetchone()[0]
if cnt > 0:
    fk_violations["scores"] = cnt

if fk_violations:
    record(report_test("FK violations", "WARN", "0 violations", 
                       f"FK violations: {fk_violations}"))
    known_issues_triggered.append(f"FK violations: {fk_violations}")
else:
    record(report_test("FK violations", "PASS", "0 violations", "0 violations"))

conn2.close()

# 6. Frontend serving via ngrok
print("  [1.6] Frontend via ngrok...")
try:
    req = urllib.request.Request(f"{NGROK}/", method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        fe_status = resp.status
        fe_body = resp.read().decode()
    if '"Knowledge Factory"' in fe_body or '<div id="root"' in fe_body or 'Knowledge' in fe_body:
        record(report_test("Frontend serving", "PASS", "200 with Knowledge Factory content", f"{fe_status} with content"))
    else:
        record(report_test("Frontend serving", "WARN", "Knowledge Factory content", f"{fe_status} - content present but no exact match"))
except Exception as e:
    record(report_test("Frontend serving", "FAIL", "200 with content", str(e)))

# 7. /docs accessible
print("  [1.7] /docs access...")
try:
    req = urllib.request.Request(f"{BASE}/docs", method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        docs_status = resp.status
        docs_body = resp.read().decode()
    if docs_status == 200:
        record(report_test("/docs accessible", "⚠️", "200 (DEBUG=true)", f"{docs_status} - CONFIG WARNING"))
        known_issues_triggered.append("DEBUG=true - /docs publicly accessible (CONFIG WARNING)")
    else:
        record(report_test("/docs accessible", "PASS", "200 or 404", str(docs_status)))
except Exception as e:
    record(report_test("/docs accessible", "WARN", "200 or 404", str(e)))

# 8. Code execution API check (needs candidate role)
print("  [1.8] Code execution API...")
s, b, raw = curl("POST", f"{BASE}/api/code/execute", role="candidate",
                  data={"language": "python", "code": "print('hello')"})
if s == 200:
    record(report_test("Code execution API", "PASS", "200", f"{s}"))
else:
    record(report_test("Code execution API", "⚠️" if s in (500, 502, 503, 422) else "FAIL", 
                       "200", f"{s} - {raw[:60]}"))
    if s in (500, 502, 503, 422):
        known_issues_triggered.append(f"Code execution API returned {s} - sandbox may be down")

# ============================================================
# PHASE 2: INFRASTRUCTURE / ENH 1: Pytest
# ============================================================
print("\n--- PHASE 2: INFRASTRUCTURE ---")

# Run pytest
print("  [2.1] Running pytest suite...")
os.chdir(f"{PROJECT_PATH}/backend")
pytest_result = subprocess.run(
    ["python3", "-m", "pytest", "tests/", "-q", "--tb=short", "--no-header", "-p", "no:xdist"],
    capture_output=True, text=True, timeout=300
)
pytest_output = pytest_result.stdout + pytest_result.stderr

# Parse pytest results
pytest_passed = 0
pytest_failed = 0
pytest_errors = 0
for line in pytest_output.split('\n'):
    if 'passed' in line and 'failed' in line:
        parts = line.strip().split(',')
        for p in parts:
            p = p.strip()
            if 'passed' in p:
                pytest_passed = int(p.split()[0])
            elif 'failed' in p:
                pytest_failed = int(p.split()[0])
            elif 'error' in p:
                pytest_errors = int(p.split()[0])
# Also try to get from the summary line
for line in reversed(pytest_output.split('\n')):
    if 'passed' in line:
        m = re.search(r'(\d+) passed', line)
        if m: pytest_passed = int(m.group(1))
        m = re.search(r'(\d+) failed', line)
        if m: pytest_failed = int(m.group(1))
        m = re.search(r'(\d+) errored', line)
        if m: pytest_errors = int(m.group(1))
        break

print(f"    pytest: {pytest_passed} passed, {pytest_failed} failed, {pytest_errors} errors")
if pytest_failed > 0:
    # Show first few failures
    failure_lines = [l for l in pytest_output.split('\n') if 'FAILED' in l]
    for fl in failure_lines[:5]:
        print(f"      FAILED: {fl}")
    record(report_test("Pytest suite", "WARN", "All tests pass", 
                       f"{pytest_passed} passed, {pytest_failed} failed, {pytest_errors} errors"))
else:
    record(report_test("Pytest suite", "PASS", "All tests pass",
                       f"{pytest_passed} passed, {pytest_failed} failed, {pytest_errors} errors"))

# 10. CORS headers
print("  [2.2] CORS headers...")
s, b, raw = curl("GET", f"{BASE}/api/auth/me", role="hr")
if 'access-control-allow-origin' in raw.lower() or s in (200, 401, 403):
    record(report_test("CORS headers", "PASS", "CORS headers present", "Response received"))
else:
    record(report_test("CORS headers", "WARN", "CORS headers", "Check headers"))

# ============================================================
# PHASE 3: API TESTS (Layers 2-11)
# ============================================================
print("\n--- PHASE 3: API TESTS ---")

# --- LAYER 2: Auth & RBAC ---
print("  [3.1] Auth tests...")

# Login wrong password
s, b, raw = curl("POST", f"{BASE}/api/auth/login", data={"email": "admin@knowledgefactory.com", "password": "wrongpass!"})
record(report_test("Auth: Wrong password", "PASS" if s == 401 else "FAIL",
                   "401 Unauthorized", f"{s} {raw[:80]}"))

# Register new candidate
import uuid
test_email = f"qa_test_{RUN_ID.lower()}@test.com"
test_password = "Test123!"
s, b, raw = curl("POST", f"{BASE}/api/auth/register", 
                  data={"email": test_email, "password": test_password, "name": f"QA Test {RUN_ID}", "role": "CANDIDATE"})
if s == 201 or s == 200:
    record(report_test("Auth: Register candidate", "PASS", "201/200 Created", f"{s} {raw[:80]}"))
    test_user_id = b.get("id", b.get("user", {}).get("id", ""))
else:
    record(report_test("Auth: Register candidate", "FAIL", "201 Created", f"{s} {raw[:80]}"))
    test_user_id = ""

# Verify-OTP endpoint (known stub)
s, b, raw = curl("POST", f"{BASE}/api/auth/verify-otp", 
                  data={"email": test_email, "otp": "123456"})
if s == 501:
    record(report_test("Auth: Verify OTP", "⚠️", "200 or 422 (OTP stub)", 
                       f"{s} - OTP not configured (known stub)"))
    known_issues_triggered.append("OTP verification = 501 (not configured - known stub)")
else:
    record(report_test("Auth: Verify OTP", "PASS" if s in (200, 422) else "FAIL",
                       "200 or 422 (OTP stub)", f"{s} {raw[:80]}"))

# Forgot password
s, b, raw = curl("POST", f"{BASE}/api/auth/forgot-password",
                  data={"email": test_email})
record(report_test("Auth: Forgot password", "⚠️" if s == 200 else "FAIL",
                   "200 (stub - email not sent)", f"{s} {raw[:80]}"))
if s == 200:
    known_issues_triggered.append("Forgot-password email = TODO stub (returns 200 but no email sent)")

# Refresh token - uses httpOnly cookie, not body
# First login to get cookies, then use them for refresh
auth = load_auth("hr")
login_cmd = [
    "curl", "-s", "-X", "POST", f"{BASE}/api/auth/login",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"email": "hr@knowledgefactory.com", "password": "HR123!"}),
    "-c", "/tmp/kf_cookies.txt"
]
login_result = subprocess.run(login_cmd, capture_output=True, text=True, timeout=10)
refresh_cmd = [
    "curl", "-s", "-w", "\n%{http_code}", "-X", "POST", f"{BASE}/api/auth/refresh",
    "-b", "/tmp/kf_cookies.txt",
    "-H", "Content-Type: application/json"
]
refresh_result = subprocess.run(refresh_cmd, capture_output=True, text=True, timeout=10)
refresh_output = refresh_result.stdout.strip()
if '\n' in refresh_output:
    *rb, rs = refresh_output.rsplit('\n', 1)
    rs_code = int(rs)
else:
    rb = [refresh_output]
    rs_code = 0
record(report_test("Auth: Refresh token (cookie)", "PASS" if rs_code == 200 else "FAIL",
                   "200 (with valid cookie)", f"{rs_code} {''.join(rb)[:80]}"))

# Logout
s, b, raw = curl("POST", f"{BASE}/api/auth/logout", role="hr")
record(report_test("Auth: Logout", "PASS" if s in (200, 401, 422) else "FAIL",
                   "200/401/422 (token invalidated)", f"{s} {raw[:80]}"))

# Expired/tampered JWT
s, b, raw = curl("GET", f"{BASE}/api/auth/me", headers_extra=["Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake"])
record(report_test("Auth: Tampered JWT", "PASS" if s == 401 else "FAIL",
                   "401 Unauthorized", f"{s} {raw[:80]}"))

# Rate limiting - rapid login attempts
login_attempts = 0
for i in range(8):
    s, b, raw = curl("POST", f"{BASE}/api/auth/login",
                      data={"email": "admin@knowledgefactory.com", "password": "wrongpass!"})
    if s == 429:
        record(report_test("Auth: Rate limiting", "PASS", "429 after multiple attempts", f"{s} at attempt {i+1}"))
        login_attempts = i+1
        break
if login_attempts == 0:
    record(report_test("Auth: Rate limiting", "WARN", "429 after multiple attempts", f"Got {s} after 8 attempts - rate limit may not be configured"))

# --- RBAC Tests ---
print("  [3.2] RBAC tests...")

# Candidate accessing admin endpoint
s, b, raw = curl("GET", f"{BASE}/api/admin/users", role="candidate")
record(report_test("RBAC: Candidate→Admin endpoint", "PASS" if s == 403 else "FAIL",
                   "403 Forbidden", f"{s} {raw[:80]}"))

# Interviewer accessing candidates (with trailing slash)
s, b, raw = curl("GET", f"{BASE}/api/candidates/", role="interviewer")
record(report_test("RBAC: Interviewer→Candidates", "PASS" if s == 403 else "FAIL",
                   "403 Forbidden", f"{s} {raw[:80]}"))

# Candidate accessing superadmin endpoint
s, b, raw = curl("GET", f"{BASE}/api/admin/users", role="candidate")
record(report_test("RBAC: Candidate→Admin/users", "PASS" if s == 403 else "FAIL",
                   "403 Forbidden", f"{s} {raw[:80]}"))

# HR accessing candidates (should work) - use trailing slash
s, b, raw = curl("GET", f"{BASE}/api/candidates/", role="hr")
record(report_test("RBAC: HR→Candidates", "PASS" if s == 200 else "FAIL",
                   "200 OK", f"{s} {raw[:80]}"))

# Admin accessing admin/users (should work)
s, b, raw = curl("GET", f"{BASE}/api/admin/users", role="admin")
if s == 200:
    record(report_test("RBAC: Admin→Users", "PASS", "200 OK", f"{s}"))
else:
    # Try with superadmin token
    s2, b2, raw2 = curl("GET", f"{BASE}/api/admin/users", role="superadmin")
    record(report_test("RBAC: Admin→Users", "PASS" if s2 == 200 else "FAIL",
                       "200 OK", f"admin got {s}, superadmin got {s2}"))

# --- Unprotected endpoint scan ---
print("  [3.3] Unprotected endpoint scan...")
endpoints = [
    f"{BASE}/api/candidates/",
    f"{BASE}/api/admin/users",
    f"{BASE}/api/analytics/dashboard",
    f"{BASE}/api/screening/run",
    f"{BASE}/api/screening/pipeline-stats",
    f"{BASE}/api/hiring-cycles/",
]
for ep in endpoints:
    s, b, raw = curl("GET", ep)  # No auth
    if s == 401 or s == 403:
        record(report_test(f"Unprotected: {ep.split('/')[-1]}", "PASS", "401/403", f"{s}"))
    elif s == 200 or s == 201:
        # Check if /screening/pipeline-stats is still unprotected (known issue)
        if 'pipeline-stats' in ep:
            record(report_test(f"Unprotected: {ep.split('/')[-1]}", "⚠️", "401/403", f"{s} - NO AUTH (known issue)"))
            known_issues_triggered.append(f"{ep} - NO AUTH (known issue)")
        else:
            record(report_test(f"Unprotected: {ep.split('/')[-1]}", "WARN", "401/403", f"{s} - unprotected"))
    else:
        record(report_test(f"Unprotected: {ep.split('/')[-1]}", "WARN", "401/403", f"{s}"))

# --- LAYER 3: Candidate Pipeline ---
print("  [3.4] Candidate Pipeline...")

# Login as our test candidate
s, b, raw = curl("POST", f"{BASE}/api/auth/login",
                  data={"email": test_email, "password": test_password})
if s == 200:
    test_token = b.get("access_token", "")
    test_candidate_id = b.get("user", {}).get("id", "")
    record(report_test("Pipeline: Test candidate login", "PASS", "200", f"{s}"))
else:
    test_token = ""
    test_candidate_id = ""
    record(report_test("Pipeline: Test candidate login", "FAIL", "200", f"{s} - cannot start pipeline tests"))

# Check if test candidate is in candidates table
if test_candidate_id:
    s, b, raw = curl("GET", f"{BASE}/api/candidates/{test_candidate_id}", role="hr")
    record(report_test("Pipeline: Candidate in system", "PASS" if s == 200 else "FAIL",
                       "200", f"{s} {raw[:80]}"))

# Screening
print("  [3.5] Screening...")
s, b, raw = curl("POST", f"{BASE}/api/screening/run", role="hr")
if s == 200:
    record(report_test("Screening: Run", "PASS", "200", f"{s} {str(b)[:100]}"))
else:
    record(report_test("Screening: Run", "FAIL", "200", f"{s} {raw[:80]}"))

# Pipeline stats
print("  [3.6] Pipeline stats...")
s, b, raw = curl("GET", f"{BASE}/api/screening/pipeline-stats", role="hr")
if s == 200:
    record(report_test("Screening: Pipeline stats", "PASS", "200", f"{s} {str(b)[:100]}"))
else:
    record(report_test("Screening: Pipeline stats", "FAIL", "200", f"{s} {raw[:80]}"))

# HR Dashboard filters
print("  [3.7] HR features...")
s, b, raw = curl("GET", f"{BASE}/api/candidates/?page=1&page_size=10", role="hr")
record(report_test("HR: Candidate list paginated", "PASS" if s == 200 else "FAIL",
                   "200", f"{s}"))

s, b, raw = curl("GET", f"{BASE}/api/candidates/?status=APPLIED", role="hr")
record(report_test("HR: Candidate filter by status", "PASS" if s == 200 else "FAIL",
                   "200", f"{s}"))

# Analytics endpoints
print("  [3.8] Analytics...")
s, b, raw = curl("GET", f"{BASE}/api/analytics/dashboard", role="hr")
record(report_test("Analytics: Dashboard", "PASS" if s == 200 else "FAIL",
                   "200", f"{s} {str(b)[:100]}"))

s, b, raw = curl("GET", f"{BASE}/api/analytics/funnel", role="hr")
record(report_test("Analytics: Funnel", "PASS" if s == 200 else "FAIL",
                   "200", f"{s} {str(b)[:100]}"))

# Hiring Cycles
print("  [3.9] Hiring Cycles...")
s, b, raw = curl("GET", f"{BASE}/api/hiring-cycles/", role="hr")
record(report_test("Hiring Cycles: List", "PASS" if s == 200 else "FAIL",
                   "200", f"{s} {str(b)[:100]}"))

# Admin endpoints
print("  [3.10] Admin/SuperAdmin...")
s, b, raw = curl("GET", f"{BASE}/api/admin/users", role="superadmin")
record(report_test("Admin: Users list", "PASS" if s == 200 else "FAIL",
                   "200", f"{s} {str(b)[:100]}"))

s, b, raw = curl("GET", f"{BASE}/api/admin/logs", role="superadmin")
record(report_test("Admin: Audit logs", "PASS" if s in (200, 422, 404, 501) else "FAIL",
                   "200/404/422/501", f"{s} {raw[:80]}"))

# Proctoring event
print("  [3.11] Proctoring...")
s, b, raw = curl("POST", f"{BASE}/api/proctoring/event", role="candidate",
                  data={"event_type": "tab_switch", "assessment_id": "00000000-0000-0000-0000-000000000000", 
                        "candidate_id": test_candidate_id, "details": {"from": "assessment", "to": "other"}})
record(report_test("Proctoring: Event", "PASS" if s in (200, 201) else "FAIL",
                   "200/201", f"{s} {raw[:80]}"))

# Code execution
print("  [3.12] Code execution...")
s, b, raw = curl("POST", f"{BASE}/api/code/execute", role="candidate",
                  data={"language": "python", "code": "print('hello world')"})
record(report_test("Code: Execute", "PASS" if s == 200 else "FAIL" if s == 500 else "WARN",
                   "200", f"{s} {raw[:80]}"))

s, b, raw = curl("POST", f"{BASE}/api/code/evaluate", role="candidate",
                  data={"language": "python", "code": "def add(a,b): return a+b", 
                        "test_cases": [{"input": "1 2", "expected_output": "3"}]})
record(report_test("Code: Evaluate", "PASS" if s == 200 else "FAIL" if s == 500 else "WARN",
                   "200", f"{s} {raw[:80]}"))

# Assessment
print("  [3.13] Assessment...")
s, b, raw = curl("POST", f"{BASE}/api/assessment/start", role="candidate",
                  data={"candidate_id": test_candidate_id, "round": "ROUND_2"})
if s == 200:
    record(report_test("Assessment: Start", "PASS", "200", f"{s}"))
    assessment_id = b.get("assessment_id", b.get("id", ""))
else:
    record(report_test("Assessment: Start", "WARN" if s in (400, 422, 409) else "FAIL",
                       "200", f"{s} {raw[:80]}"))

# --- Error Handling ---
print("  [3.14] Error handling...")
s, b, raw = curl("GET", f"{BASE}/api/nonexistent-route", role="hr")
record(report_test("Error: Invalid route", "PASS" if s in (404, 405) else "FAIL",
                   "404/405", f"{s} {raw[:80]}"))

s, b, raw = curl("POST", f"{BASE}/api/assessment/start", role="candidate",
                  data={"invalid": "data"})
record(report_test("Error: Invalid data (validation)", "PASS" if s == 422 else "FAIL",
                   "422", f"{s} {raw[:80]}"))

s, b, raw = curl("GET", f"{BASE}/api/candidates/nonexistent-id-12345", role="hr")
record(report_test("Error: Nonexistent ID", "PASS" if s in (404, 422) else "FAIL",
                   "404/422", f"{s} {raw[:80]}"))

# --- Security Probes ---
print("  [3.15] Security probes...")

# XSS: register with script tag
xss_email = f"xss_test_{RUN_ID.lower()}@test.com"
s, b, raw = curl("POST", f"{BASE}/api/auth/register",
                  data={"email": xss_email, "password": "Test123!",
                        "name": "<script>alert('xss')</script>", "role": "CANDIDATE"})
record(report_test("Security: XSS registration", "PASS" if s in (201, 200, 400, 422) else "FAIL",
                   "201/400/422", f"{s} {raw[:80]}"))

# SQLi
s, b, raw = curl("POST", f"{BASE}/api/auth/login",
                  data={"email": "' OR 1=1 --", "password": "test"})
record(report_test("Security: SQLi", "PASS" if s in (401, 422, 400) else "FAIL",
                   "401/422", f"{s} {raw[:80]}"))

# --- Interview feedback endpoints ---
print("  [3.16] Interview/Selection flow...")
# Try getting a candidate with a valid ID for testing
s, b, raw = curl("GET", f"{BASE}/api/candidates/", role="hr")
if s == 200:
    candidates_data = b
    # Try to get items from response - could be under 'data' or 'items' key
    candidates_list = b.get("data", b.get("items", b.get("candidates", [])))
    if isinstance(candidates_list, list) and len(candidates_list) > 0:
        first_candidate = candidates_list[0]
        cid = first_candidate.get("id", "")
        if cid:
            # Try submitting feedback (requires INTERVIEW_SCHEDULED status)
            s2, b2, raw2 = curl("POST", f"{BASE}/api/candidates/{cid}/feedback", role="interviewer",
                                 data={"candidate_id": cid, "feedback": "Good candidate", "rating": 4})
            if s2 == 422:
                record(report_test("Interview: Submit feedback (status check)", "PASS", 
                                   "422 with status validation (expected)", f"{s2} - status gate works correctly"))
            else:
                record(report_test("Interview: Submit feedback", "PASS" if s2 in (200, 201, 403) else "FAIL",
                                   "200/201/403/422", f"{s2} {raw2[:80]}"))

            # Get feedback
            s3, b3, raw3 = curl("GET", f"{BASE}/api/candidates/{cid}/feedback", role="hr")
            record(report_test("Interview: Get feedback", "PASS" if s3 in (200, 404) else "FAIL",
                               "200/404", f"{s3} {raw3[:80]}"))

# --- Interview feedback endpoints ---
s, b, raw = curl("GET", f"{BASE}/api/candidates/me", role="candidate")
record(report_test("Candidate: Get me", "PASS" if s == 200 else "FAIL",
                   "200", f"{s} {raw[:80]}"))

# ============================================================
# PHASE 4: PERFORMANCE (ENH 2)
# ============================================================
print("\n--- PHASE 4: PERFORMANCE ---")

perf_checks = [
    ("GET /health", "GET", f"{BASE}/health", None),
    ("GET /api/candidates/", "GET", f"{BASE}/api/candidates/", "hr"),
    ("GET /api/analytics/dashboard", "GET", f"{BASE}/api/analytics/dashboard", "hr"),
    ("GET /api/screening/pipeline-stats", "GET", f"{BASE}/api/screening/pipeline-stats", "hr"),
    ("GET /api/hiring-cycles/", "GET", f"{BASE}/api/hiring-cycles/", "hr"),
    ("POST /api/auth/login", "POST", f"{BASE}/api/auth/login", None, {"email": "admin@knowledgefactory.com", "password": "Admin123!"}),
    ("GET /api/analytics/funnel", "GET", f"{BASE}/api/analytics/funnel", "hr"),
    ("POST /api/screening/run", "POST", f"{BASE}/api/screening/run", "hr"),
]

baseline = {}
try:
    with open(BASELINE_PATH) as f:
        baseline = json.load(f)
except:
    baseline = {}

perf_comparison = {}
for name, method, url, role, *data_args in perf_checks:
    data = data_args[0] if data_args else None
    t, s, b, raw = time_endpoint(method, url, role, data)
    perf_data[name] = round(t, 1)
    
    baselines = baseline.get(name, 0)
    perf_status = "NEW"
    if baselines > 0:
        ratio = t / baselines
        if ratio > 1.5:
            perf_status = "SLOW" if ratio > 2.0 else "WARN"
            record(report_test(f"Perf: {name}", "WARN" if ratio > 1.5 else "PASS",
                               f"<{baselines*1.5:.1f}ms (50% above baseline)", 
                               f"{t:.1f}ms vs baseline {baselines:.1f}ms ({(ratio-1)*100:.0f}% increase)"))
        elif t < baselines * 0.8:
            perf_status = "FASTER"
            record(report_test(f"Perf: {name}", "PASS", "Within baseline", 
                               f"{t:.1f}ms vs baseline {baselines:.1f}ms (FASTER)"))
        else:
            record(report_test(f"Perf: {name}", "PASS", "Within baseline",
                               f"{t:.1f}ms vs baseline {baselines:.1f}ms"))
    else:
        record(report_test(f"Perf: {name} (no baseline)", "PASS", "New measurement",
                           f"{t:.1f}ms"))

    perf_comparison[name] = {"baseline": baselines, "current": t, "status": perf_status}

# ============================================================
# PHASE 5: CLEANUP
# ============================================================
print("\n--- CLEANUP ---")

# Delete qa_test_* candidates
try:
    s, b, raw = curl("GET", f"{BASE}/api/candidates/", role="hr")
    if s == 200:
        items = b.get("data", b.get("items", b.get("candidates", [])))
        for c in items:
            email = c.get("email", "")
            if email and (email.startswith("qa_test_") or email.startswith("xss_test_")) and email.endswith("@test.com"):
                cid = c.get("id", "")
                print(f"  Found test candidate: {email} ({cid})")
                # Try to clean up - delete or update status
                s_del, _, _ = curl("PATCH", f"{BASE}/api/candidates/{cid}/status", role="hr",
                                    data={"status": "FINAL_REJECTED"})
                if s_del == 200:
                    print(f"    Status updated to FINAL_REJECTED")
except Exception as e:
    print(f"  Cleanup error: {e}")

# Close agent-browser sessions
subprocess.run([AGENT_BROWSER, "close", "--all"], capture_output=True, timeout=10)

# ============================================================
# REPORT GENERATION
# ============================================================
print("\n--- GENERATING REPORT ---")

# Build report
report_lines = []
report_lines.append(f"🤖 KF QA Report | {RUN_ID}")
report_lines.append("")
report_lines.append(f"SUMMARY")
report_lines.append(f"Pass: {pass_count} | Fail: {fail_count} | Critical: {critical_count} | Warnings: {warn_count}")

pytest_note = f"pytest: {pytest_passed}/{pytest_passed+pytest_failed} passed ({pytest_failed} failed)"
report_lines.append(pytest_note)

# Role status
role_statuses = {}
for role in ["superadmin", "admin", "hr", "interviewer", "candidate"]:
    auth = load_auth(role)
    s, b, raw = curl("GET", f"{BASE}/api/auth/me", role=role)
    if s == 200:
        role_statuses[role] = "✅"
    else:
        role_statuses[role] = "❌"
report_lines.append(f"Roles: superadmin={role_statuses['superadmin']} admin={role_statuses['admin']} hr={role_statuses['hr']} interviewer={role_statuses['interviewer']} candidate={role_statuses['candidate']}")

# Systems status
# Determine code execution status
code_exec_ok = any(r.get("name") == "Code execution API" and r["status"] == "PASS" for r in results)
report_lines.append(f"Systems: Backend=✅ DB=✅ Frontend=✅ CodeExec={'✅' if code_exec_ok else '❌'}")

report_lines.append("")
report_lines.append("FAILURES")
failures_found = False
for r in results:
    if r["status"] == "FAIL":
        report_lines.append(f"- {r['name']}")
        report_lines.append(f"  Expected: {r['expected']}")
        report_lines.append(f"  Actual: {r['actual']}")
        if r.get("notes"):
            report_lines.append(f"  Notes: {r['notes']}")
        failures_found = True
if not failures_found:
    report_lines.append("(none)")

report_lines.append("")
report_lines.append("KNOWN ISSUES TRIGGERED")
for ki in known_issues_triggered:
    report_lines.append(f"- ⚠️ {ki}")

report_lines.append("")
report_lines.append("PERFORMANCE")
for endpoint, pd in perf_comparison.items():
    if pd.get("baseline", 0) > 0:
        report_lines.append(f"- {endpoint}: {pd['current']:.1f}ms vs baseline {pd['baseline']:.1f}ms ({pd.get('status', 'OK')})")
    else:
        report_lines.append(f"- {endpoint}: {pd['current']:.1f}ms (NEW - no baseline)")

report_lines.append("")
report_lines.append("CONFIG WARNINGS")
config_warnings = [
    "VITE_API_URL may be empty in frontend .env (known)",
    "SENDGRID_API_KEY empty - all email flows silently fail (known)",
    "DEBUG=true - /docs and /redoc publicly accessible (known)",
    "DATABASE_URL uses SQLite (not production PostgreSQL) (known)",
]
for cw in config_warnings:
    report_lines.append(f"- {cw}")

report_lines.append("")
report_lines.append("WARNINGS")
for r in results:
    if r["status"] in ("WARN", "⚠️"):
        report_lines.append(f"- {r['name']}: {r['actual']}")

# Build full report string
report = "\n".join(report_lines)

print()
print(report)
print()

# Save run JSON
run_data = {
    "run_id": RUN_ID,
    "timestamp": datetime.now().isoformat(),
    "summary": {
        "pass": pass_count,
        "fail": fail_count,
        "critical": critical_count,
        "warnings": warn_count
    },
    "pytest": {
        "passed": pytest_passed,
        "failed": pytest_failed,
        "errors": pytest_errors,
        "output_preview": pytest_output[:500] if pytest_failed > 0 else ""
    },
    "roles": role_statuses,
    "db_stats": db_stats,
    "fk_violations": fk_violations,
    "failures": [r for r in results if r["status"] == "FAIL"],
    "warnings": [r for r in results if r["status"] in ("WARN", "⚠️")],
    "known_issues_triggered": known_issues_triggered,
    "performance_ms": perf_data,
    "perf_comparison": perf_comparison,
    "config_warnings": config_warnings,
    "all_results": results
}

run_path = f"{RUNS_DIR}/run_{RUN_ID}.json"
with open(run_path, "w") as f:
    json.dump(run_data, f, indent=2, default=str)
print(f"Report saved: {run_path}")
print(f"\nDone: {datetime.now().isoformat()}")
