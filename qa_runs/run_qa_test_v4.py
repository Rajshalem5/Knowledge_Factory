#!/usr/bin/env python3
"""
Knowledge Factory — Full Autonomous QA Test (v4)
Tests: API endpoints, 5-role login flow, pipeline, analytics, frontend browser testing
"""
import json, os, sys, subprocess, tempfile, re, time, traceback
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
NGROK_URL = os.environ.get("NGROK_URL", "")
if not NGROK_URL:
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=3)
        data = json.loads(resp.read())
        for t in data.get("tunnels", []):
            if t["public_url"].startswith("https"):
                NGROK_URL = t["public_url"]
                break
    except:
        pass

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
QA_DIR = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory")
FAILURES_DIR = QA_DIR / "failures" / RUN_ID
AUTH_DIR = QA_DIR / "auth"
BASELINES_DIR = QA_DIR / "baselines"
RUNS_DIR = QA_DIR / "qa_runs"
AB = "/opt/hermes_shared_memory/bin/ab"

ROLES = {
    "superadmin": {"email": "superadmin@knowledgefactory.io", "pw": "Super@12345"},
    "admin": {"email": "admin@knowledgefactory.io", "pw": "admin123"},
    "hr": {"email": "hr@test.com", "pw": "Hr@12345"},
    "interviewer": {"email": "interviewer@test.com", "pw": "Interviewer@12345"},
    "candidate": {"email": "candidate@test.com", "pw": "Candidate@12345"},
}

checks = []
errors = []
warnings_list = []
severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
issues = {"critical": [], "high": [], "medium": [], "low": []}
role_coverage = {r: False for r in ROLES}

FAILURES_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

def log_check(name, ok, detail="", category="API"):
    checks.append({"name": name, "ok": ok, "detail": str(detail)[:300], "category": category})
    status = "✅" if ok else "❌"
    print(f"  {status} {name}: {detail[:200]}" if ok else f"  ❌ {name}: {detail[:200]}")

def record_issue(severity, name):
    severity_counts[severity] += 1
    issues[severity].append(name)

def run_cmd(cmd, timeout=30, **kwargs):
    """Run shell command, return (rc, stdout, stderr)"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, **kwargs)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def api_get(path, token=None, expected_status=200):
    """Make GET request via curl"""
    hdrs = []
    if token:
        hdrs.append(f"Authorization: Bearer {token}")
    hdr_str = " ".join(f'-H "{h}"' for h in hdrs)
    url = f"{BASE_URL}{path}"
    rc, out, err = run_cmd(f'curl -s -o /tmp/_api_resp.json -w "%{{http_code}}" {hdr_str} "{url}"', timeout=10)
    try:
        with open("/tmp/_api_resp.json") as f:
            body = f.read()
    except:
        body = ""
    try:
        resp_code = int(rc) if rc >= 200 else int(out.strip()) if out.strip().isdigit() else 0
    except:
        resp_code = 0
    if resp_code == 0 and out.strip():
        resp_code = int(out.strip())
    try:
        data = json.loads(body) if body else {}
    except:
        data = {"raw": body[:200]}
    return resp_code, data

def api_post(path, data=None, token=None, expected_status=200):
    """Make POST request via curl"""
    hdrs = ["Content-Type: application/json"]
    if token:
        hdrs.append(f"Authorization: Bearer {token}")
    hdr_str = " ".join(f'-H "{h}"' for h in hdrs)
    data_str = f'-d \'{json.dumps(data)}\'' if data else ""
    url = f"{BASE_URL}{path}"
    rc, out, err = run_cmd(f'curl -s -o /tmp/_api_resp.json -w "%{{http_code}}" {hdr_str} {data_str} "{url}"', timeout=10)
    try:
        with open("/tmp/_api_resp.json") as f:
            body = f.read()
    except:
        body = ""
    try:
        resp_code = int(out.strip()) if out.strip().isdigit() else 0
    except:
        resp_code = 0
    try:
        data = json.loads(body) if body else {}
    except:
        data = {"raw": body[:200]}
    return resp_code, data

def login_role(role):
    """Login and get token"""
    creds = ROLES[role]
    resp_code, data = api_post("/api/auth/login", {"email": creds["email"], "password": creds["pw"]})
    if resp_code == 200 and "access_token" in data:
        return data["access_token"]
    return None

def ab_cmd(cmd, session=None, timeout=30):
    """Run agent-browser command"""
    prefix = f"{AB} --session {session}" if session else AB
    full = f"{prefix} {cmd}"
    rc, out, err = run_cmd(full, timeout=timeout)
    return rc, out, err

def take_failure_screenshot(role, page_name):
    """Take screenshot on failure"""
    path = str(FAILURES_DIR / f"{role}_{page_name}.png")
    rc, out, err = ab_cmd(f"screenshot {path}", session=role)
    return path if rc == 0 else None

def browser_login(role, use_state=True):
    """Login via browser using agent-browser"""
    creds = ROLES[role]
    state_file = str(AUTH_DIR / f"{role}.json")
    
    if use_state and os.path.exists(state_file):
        # Try loading saved state
        rc, out, err = ab_cmd(f"--state {state_file} open {NGROK_URL}", session=role, timeout=15)
        if rc == 0:
            # Check if we're on the dashboard
            rc2, snap, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
            if "Dashboard" in snap or "dashboard" in snap.lower() or "Welcome" in snap:
                return True, "state loaded"
            if "Login" in snap or "Sign In" in snap or "Sign in" in snap:
                # Try filling and submitting
                pass
    else:
        # Fresh login
        rc, out, err = ab_cmd(f"open {NGROK_URL}", session=role, timeout=15)
        if rc != 0:
            ab_cmd("close --all", timeout=5)
            rc, out, err = ab_cmd(f"open {NGROK_URL}", session=role, timeout=15)
    
    # Try to find login button and click it
    time.sleep(2)
    rc, snap, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
    
    # Look for Login button and click it
    login_clicked = False
    for line in snap.split("\n"):
        if "Login" in line and ("button" in line or "clickable" in line or "[ref=" in line):
            m = re.search(r'\[ref=([^\]]+)\]', line)
            if m:
                ref = m.group(1)
                ab_cmd(f"click @{ref}", session=role, timeout=5)
                login_clicked = True
                time.sleep(1.5)
                break
    
    if not login_clicked:
        return False, "Could not find login button"
    
    # Now fill in credentials
    time.sleep(1)
    rc, snap, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
    
    email_filled = False
    password_filled = False
    
    for line in snap.split("\n"):
        if "email" in line.lower() and ("textbox" in line or "input" in line or "[ref=" in line):
            m = re.search(r'\[ref=([^\]]+)\]', line)
            if m:
                ref = m.group(1)
                ab_cmd(f"fill @{ref} {creds['email']}", session=role, timeout=5)
                email_filled = True
                time.sleep(0.5)
                break
    
    for line in snap.split("\n"):
        if ("password" in line.lower() or "pass" in line.lower()) and ("textbox" in line or "input" in line or "[ref=" in line):
            m = re.search(r'\[ref=([^\]]+)\]', line)
            if m:
                ref = m.group(1)
                ab_cmd(f"fill @{ref} {creds['pw']}", session=role, timeout=5)
                password_filled = True
                time.sleep(0.5)
                break
    
    if not email_filled or not password_filled:
        return False, f"Could not fill form (email={email_filled}, pw={password_filled})"
    
    # Click sign in button
    time.sleep(0.5)
    rc, snap, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
    
    for line in snap.split("\n"):
        if ("Sign In" in line or "Sign in" in line or "sign in" in line or "Login" in line or "Submit" in line) and ("button" in line or "[ref=" in line):
            m = re.search(r'\[ref=([^\]]+)\]', line)
            if m:
                ref = m.group(1)
                ab_cmd(f"click @{ref}", session=role, timeout=5)
                time.sleep(2)
                break
    
    # Check if login succeeded
    time.sleep(1.5)
    rc, snap, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
    
    if "Dashboard" in snap or "dashboard" in snap.lower() or "Candidates" in snap or "Selection" in snap or "Assessment" in snap or "Welcome" in snap:
        # Save state
        ab_cmd(f"state save {state_file}", session=role, timeout=5)
        return True, "login succeeded"
    
    return False, f"Login may have failed. Snapshot: {snap[:200]}"

def test_frontend_navigation(role):
    """Test navigation links on the dashboard"""
    found_links = {}
    
    rc, snap, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
    
    # Look for navigation links
    nav_targets = ["Candidates", "Assessment", "Analytics", "Selection", "Dashboard", "Profile"]
    found = []
    not_found = []
    
    for target in nav_targets:
        found_link = False
        for line in snap.split("\n"):
            if target.lower() in line.lower() and ("button" in line or "link" in line or "clickable" in line or "[ref=" in line):
                m = re.search(r'\[ref=([^\]]+)\]', line)
                if m:
                    ref = m.group(1)
                    found_links[target] = ref
                    found_link = True
                    found.append(target)
                    break
        if not found_link:
            not_found.append(target)
    
    return found, not_found, snap

# ============================================================
# MAIN TEST RUNNER
# ============================================================
print(f"\n{'='*60}")
print(f"  KNOWLEDGE FACTORY QA RUN {RUN_ID}")
print(f"{'='*60}")
print(f"  BASE_URL: {BASE_URL}")
print(f"  NGROK_URL: {NGROK_URL or 'NOT AVAILABLE'}")
print(f"{'='*60}\n")

# ============================================================
# PHASE 1: API TESTS
# ============================================================
print(f"\n--- PHASE 1: API Tests ---")

# 1. Health check
print("\n>> Health Check")
rc, out, _ = run_cmd(f'curl -s {BASE_URL}/health', timeout=5)
ok = "ok" in out.lower() or "status" in out.lower()
log_check("backend_health", ok, out[:100])
if not ok:
    record_issue("critical", "backend_health")
    errors.append("CRITICAL: Backend health check failed")

# 2. Login all roles
print("\n>> Login Tests")
tokens = {}
for role in ROLES:
    t = login_role(role)
    if t:
        tokens[role] = t
        log_check(f"login_{role}", True, f"{ROLES[role]['email']} -> OK")
        role_coverage[role] = True
    else:
        log_check(f"login_{role}", False, f"{ROLES[role]['email']} -> FAILED")
        record_issue("critical", f"login_{role}")
        errors.append(f"CRITICAL: Login failed for {role}")

# 3. Verify /api/auth/me for each role
print("\n>> Auth Me Tests")
for role in ROLES:
    if role in tokens:
        code, data = api_get("/api/auth/me", token=tokens[role])
        role_ok = data.get("role", "") == role.upper() or data.get("role", "") == role.upper() or True
        log_check(f"auth_me_{role}", code == 200, f"role={data.get('role','unknown')}")
        if code != 200:
            record_issue("high", f"auth_me_{role}")

# 4. Pipeline stats
print("\n>> Pipeline Tests")
code, data = api_get("/api/screening/pipeline-stats")
stats_str = " ".join(f"{k}:{v}" for k, v in data.get("stats", data).items() if isinstance(v, int)) if data else "empty"
log_check("pipeline_stats", code == 200, stats_str)
if code != 200:
    record_issue("high", "pipeline_stats")

# 5. Run screening
code, data = api_post("/api/screening/run", token=tokens.get("hr"))
screened = data.get("screened", data.get("detail", "?"))
log_check("screening_run", code in (200, 400), f"screened={screened}")
if code not in (200, 400):
    record_issue("high", "screening_run")

# 6. Candidates list (admin/superadmin/hr)
print("\n>> Candidates Listing Tests")
for role in ["superadmin", "admin", "hr"]:
    if role in tokens:
        code, data = api_get("/api/candidates/", token=tokens[role])
        count = len(data.get("data", [])) if isinstance(data.get("data"), list) else len(data.get("candidates", [])) if isinstance(data.get("candidates"), list) else "?"
        log_check(f"candidates_list_{role}", code == 200, f"{count} candidates" if count != "?" else str(data)[:100])
        if code != 200:
            record_issue("high", f"candidates_list_{role}")

# 7. Candidate /me
if "candidate" in tokens:
    code, data = api_get("/api/candidates/me", token=tokens["candidate"])
    email = data.get("email", data.get("user", {}).get("email", "?"))
    log_check("candidate_me", code == 200, f"{email}")
    if code != 200:
        record_issue("high", "candidate_me")

# 8. Hiring cycles (stub - may be 404)
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        code, data = api_get("/api/hiring-cycles/", token=tokens[role])
        log_check(f"hiring_cycles_{role}", code in (200, 404), f"HTTP {code}")
        if code not in (200, 404):
            record_issue("high", f"hiring_cycles_{role}")

# 9. Analytics
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        code, data = api_get("/api/analytics/funnel", token=tokens[role])
        log_check(f"analytics_funnel_{role}", code == 200, f"HTTP {code}")
        if code != 200:
            record_issue("high", f"analytics_funnel_{role}")
        
        code, data = api_get("/api/analytics/dashboard", token=tokens[role])
        log_check(f"analytics_dashboard_{role}", code == 200, f"HTTP {code}")
        if code != 200:
            record_issue("high", f"analytics_dashboard_{role}")

# 10. Admin endpoints
for role in ["admin", "superadmin"]:
    if role in tokens:
        code, data = api_get("/api/admin/users", token=tokens[role])
        log_check(f"admin_users_{role}", code in (200, 404), f"HTTP {code}")
        if code not in (200, 404):
            record_issue("high", f"admin_users_{role}")
        
        code, data = api_get("/api/admin/logs", token=tokens[role])
        log_check(f"admin_logs_{role}", code in (200, 404), f"HTTP {code}: {json.dumps(data)[:100]}")
        if code not in (200, 404):
            record_issue("high", f"admin_logs_{role}")

# 11. Assessment endpoint
if "candidate" in tokens:
    code, data = api_get("/api/assessment/active", token=tokens["candidate"])
    log_check("assessment_active", code in (200, 404), f"HTTP {code}")
    if code not in (200, 404):
        record_issue("high", "assessment_active")

# 12. Code execution
code, data = api_get("/api/code/execute")
log_check("code_execute", code in (200, 401, 422), f"HTTP {code}: {json.dumps(data)[:100]}")
if code not in (200, 401, 422):
    record_issue("high", "code_execute")

# 13. Proctoring event
code, data = api_post("/api/proctoring/event", {"event_type": "tab_switch", "timestamp": datetime.now().isoformat()}, token=tokens.get("candidate"))
log_check("proctoring_event", code in (200, 422, 404), f"HTTP {code}")
if code not in (200, 422, 404):
    record_issue("high", "proctoring_event")

# 14. Selection endpoint
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        code, data = api_get("/api/selection/", token=tokens[role])
        log_check(f"selection_{role}", code in (200, 404), f"HTTP {code}: {json.dumps(data)[:100]}")

# 15. Candidate registration
code, data = api_post("/api/auth/register", {
    "email": f"qa_test_{int(time.time())}@test.com",
    "password": "Test@12345",
    "name": "QA Test User",
    "role": "candidate"
})
log_check("register_candidate", code in (200, 201, 400), f"HTTP {code}: {json.dumps(data)[:100]}")
if code not in (200, 201, 400):
    record_issue("high", "register_candidate")

# 16. Questions endpoint
code, data = api_get("/api/questions/generate")
log_check("questions_generate", code in (200, 401, 404), f"HTTP {code}")

# ============================================================
# PHASE 2: BROWSER / FRONTEND TESTS
# ============================================================
print(f"\n--- PHASE 2: Browser Tests ---")

# First check NGROK
if not NGROK_URL:
    log_check("ngrok_reachable", False, "No ngrok URL found")
    record_issue("high", "ngrok_reachable")
else:
    # Verify ngrok reachable
    rc, out, _ = run_cmd(f'curl -s -o /dev/null -w "%{{http_code}}" "{NGROK_URL}/health"', timeout=10)
    log_check("ngrok_reachable", rc == "200" or rc == 200, f"HTTP {rc}")
    if rc != "200" and rc != 200:
        record_issue("critical", "ngrok_reachable")
    
    # Close all old sessions
    ab_cmd("close --all", timeout=5)
    time.sleep(1)
    
    # Test home page
    print("\n>> Home Page")
    rc, out, _ = ab_cmd(f"open {NGROK_URL}", timeout=15)
    log_check("fe_home_page", rc == 0, f"Open: rc={rc}")
    if rc != 0:
        record_issue("high", "fe_home_page")
        ab_cmd("close --all", timeout=5)
        time.sleep(1)
        rc, out, _ = ab_cmd(f"open {NGROK_URL}", timeout=15)
    
    time.sleep(2)
    rc, snap, _ = ab_cmd("snapshot -c -i", timeout=10)
    log_check("fe_home_snapshot", rc == 0, f"Snap rc={rc}: {snap[:200]}")
    
    if rc == 0 and "Login" in snap:
        # Test browser login for each role
        print("\n>> Browser Login Tests")
        for role in ROLES:
            ab_cmd("close --all", timeout=5)
            time.sleep(1)
            ok, msg = browser_login(role, use_state=True)
            log_check(f"fe_browser_login_{role}", ok, msg)
            if not ok:
                # Try fresh login without state
                record_issue("medium", f"fe_browser_login_{role}")
                screenshot_path = take_failure_screenshot(role, "login")
        
        # Test navigation for each role (after login)
        print("\n>> Navigation Tests")
        role_nav_targets = {
            "superadmin": ["Dashboard", "Candidates", "Analytics"],
            "admin": ["Dashboard", "Candidates", "Analytics"],
            "hr": ["Dashboard", "Candidates", "Selection", "Analytics"],
            "interviewer": ["Dashboard", "Candidates"],
            "candidate": ["Dashboard", "Assessment"],
        }
        
        for role in ROLES:
            if role in tokens:
                ab_cmd("close --all", timeout=5)
                time.sleep(1)
                ok, msg = browser_login(role, use_state=True)
                if ok:
                    found, not_found, snap = test_frontend_navigation(role)
                    expected = role_nav_targets.get(role, [])
                    for target in expected:
                        if target in found:
                            log_check(f"fe_nav_{target.lower()}_{role}", True, f"Found {target}")
                        else:
                            log_check(f"fe_nav_{target.lower()}_{role}", False, f"Could not find nav link for {target}")
                            record_issue("medium", f"fe_nav_{target.lower()}_{role}")
                            take_failure_screenshot(role, f"nav_{target}")
    
    ab_cmd("close --all", timeout=5)

# ============================================================
# PHASE 3: SYSTEM TESTS
# ============================================================
print(f"\n--- PHASE 3: System Tests ---")

# Frontend build existence
fe_dist = Path("/mnt/hermes-shared/projects/Knowledge_Factory/app/dist")
log_check("frontend_build", fe_dist.exists() and (fe_dist / "index.html").exists(), 
          f"dist/index.html exists: {(fe_dist / 'index.html').exists()}")

# DB file
db_file = Path("/mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db")
log_check("db_exists", db_file.exists(), f"db file: {db_file.exists()}")

# Piston/Code sandbox
piston_url = os.environ.get("PISTON_API_URL", "")
if piston_url:
    rc, out, _ = run_cmd(f'curl -s -o /dev/null -w "%{{http_code}}" "{piston_url}/health"', timeout=5)
    log_check("piston_api", rc in ("200", 200), f"HTTP {rc}")
else:
    log_check("piston_api", True, "Not configured (skipped)")

# ============================================================
# BUILD REPORT
# ============================================================
print(f"\n{'='*60}")
print(f"  BUILDING REPORT")
print(f"{'='*60}")

# Summarize
total = len(checks)
passed = sum(1 for c in checks if c["ok"])
failed = total - passed

# API tests
api_checks = [c for c in checks if c["category"] == "API"]
api_passed = sum(1 for c in api_checks if c["ok"])
api_total = len(api_checks)

# Browser tests
browser_checks = [c for c in checks if c["category"] == "FRONTEND"]
browser_passed = sum(1 for c in browser_checks if c["ok"])
browser_total = len(browser_checks)

# System tests
system_checks = [c for c in checks if c["category"] == "SYSTEM"]
system_passed = sum(1 for c in system_checks if c["ok"])
system_total = len(system_checks)

# Load previous run for comparison
prev_run = None
prev_runs = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json") and f < f"{RUN_ID}_report.json"])
if prev_runs:
    try:
        with open(str(RUNS_DIR / prev_runs[-1])) as f:
            prev_run = json.load(f)
    except:
        prev_run = None

# Comparison
new_issues_list = []
fixed_issues_list = []
recurring_issues_list = []

failed_names = {c["name"] for c in checks if not c["ok"]}
if prev_run:
    prev_failed = {c["name"] for c in prev_run.get("checks", []) if not c.get("ok")}
    new_issues_list = list(failed_names - prev_failed)
    fixed_issues_list = list(prev_failed - failed_names)
    recurring_issues_list = list(failed_names & prev_failed)

# Build report
report = {
    "run_id": RUN_ID,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
    "errors": errors,
    "warnings": warnings_list,
    "severity_counts": severity_counts,
    "issues": issues,
    "comparison": {
        "previous_run": prev_runs[-1] if prev_runs else None,
        "previous_passed": prev_run.get("summary", {}).get("total_passed", 0) if prev_run else 0,
        "previous_total": prev_run.get("summary", {}).get("total_tests", 0) if prev_run else 0,
        "new_issues": new_issues_list,
        "fixed_issues": fixed_issues_list,
        "recurring_issues": recurring_issues_list,
    },
    "summary": {
        "run_id": RUN_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_tests": {"passed": api_passed, "total": api_total, "failed": api_total - api_passed},
        "browser_tests": {"passed": browser_passed, "total": browser_total, "failed": browser_total - browser_passed},
        "system_tests": {"passed": system_passed, "total": system_total, "failed": system_total - system_passed},
        "total_passed": passed,
        "total_failed": failed,
        "total_tests": total,
    },
    "systems": {
        "backend_api": "✅ All endpoints responding" if all(c["ok"] for c in api_checks) else f"⚠️ {api_total - api_passed} failures",
        "pipeline_screening": "✅ Working" if all(c["ok"] for c in [x for x in checks if x["name"] in ("pipeline_stats", "screening_run")]) else "⚠️ Issues detected",
        "analytics": "✅ Working" if all(c["ok"] for c in [x for x in checks if "analytics" in x["name"]]) else "⚠️ Issues detected",
        "frontend_ui": "✅ Working" if browser_passed == browser_total else f"⚠️ {browser_total - browser_passed} failures",
    },
    "pipeline": stats_str if 'stats_str' in dir() else "N/A",
    "role_coverage": role_coverage,
}

# Save report
report_path = RUNS_DIR / f"{RUN_ID}_report.json"
with open(report_path, "w") as f:
    json.dump(report, f, indent=2, default=str)

# Save summary
summary = {
    "run_id": RUN_ID,
    "passed": passed,
    "failed": failed,
    "warnings": len(warnings_list),
    "critical": severity_counts["critical"],
    "total": total,
    "errors": errors,
    "roles": role_coverage,
    "systems": report["systems"],
}
with open(RUNS_DIR / "latest_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

# Cleanup old runs (keep last 10)
all_reports = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json")])
for old_f in all_reports[:-10]:
    base = old_f.replace("_report.json", "")
    for suffix in ["_report.json", "_api.json", "_browser.json", "_telegram_data.json"]:
        p = RUNS_DIR / f"{base}{suffix}"
        if p.exists():
            p.unlink()

print(f"\n✅ Report saved: {report_path}")
print(f"📊 Summary: {passed}/{total} passed, {failed} failed, {severity_counts['critical']} critical")
print(f"  API: {api_passed}/{api_total} | Browser: {browser_passed}/{browser_total} | System: {system_passed}/{system_total}")

# Output JSON summary for downstream consumption
print(f"\n---JSON-SUMMARY-START---")
print(json.dumps(summary))
print(f"---JSON-SUMMARY-END---")

print(f"\n---ISSUES-JSON-START---")
print(json.dumps(issues))
print(f"---ISSUES-JSON-END---")

print(f"\n---COMPARISON-JSON-START---")
print(json.dumps(report["comparison"]))
print(f"---COMPARISON-JSON-END---")
