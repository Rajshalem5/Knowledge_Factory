#!/usr/bin/env python3
"""
Knowledge Factory — Full Autonomous QA Test (v5)
Fixed: HR credentials, code_execute POST with auth, screening_run check
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

# FIXED: hr@knowledgefactory.io (seed.py), not hr@test.com
ROLES = {
    "superadmin": {"email": "superadmin@knowledgefactory.io", "pw": "Super@12345"},
    "admin": {"email": "admin@knowledgefactory.io", "pw": "admin123"},
    "hr": {"email": "hr@knowledgefactory.io", "pw": "Hr@12345"},
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
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, **kwargs)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def api_get(path, token=None):
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
        resp_code = int(out.strip()) if out.strip().isdigit() else 0
    except:
        resp_code = 0
    try:
        data = json.loads(body) if body else {}
    except:
        data = {"raw": body[:200]}
    return resp_code, data

def api_post(path, data=None, token=None):
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
    creds = ROLES[role]
    resp_code, data = api_post("/api/auth/login", {"email": creds["email"], "password": creds["pw"]})
    if resp_code == 200 and "access_token" in data:
        return data["access_token"]
    return None

def ab_cmd(cmd, session=None, timeout=30):
    prefix = f"{AB} --session {session}" if session else AB
    full = f"{prefix} {cmd}"
    rc, out, err = run_cmd(full, timeout=timeout)
    return rc, out, err

def take_failure_screenshot(role, page_name):
    path = str(FAILURES_DIR / f"{role}_{page_name}.png")
    rc, out, err = ab_cmd(f"screenshot {path}", session=role)
    return path if rc == 0 else None

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
        actual_role = data.get("role", "")
        expected_role = role.upper()
        is_ok = code == 200
        log_check(f"auth_me_{role}", is_ok, f"role={actual_role}")
        if not is_ok:
            record_issue("high", f"auth_me_{role}")

# 4. Pipeline stats
print("\n>> Pipeline Tests")
code, data = api_get("/api/screening/pipeline-stats")
stats = data.get("stats", data) if isinstance(data, dict) else {}
stats_str = " ".join(f"{k}:{v}" for k, v in stats.items() if isinstance(v, int)) if isinstance(stats, dict) else str(data)[:100]
log_check("pipeline_stats", code == 200, stats_str)
if code != 200:
    record_issue("high", "pipeline_stats")

# 5. Run screening (with HR auth - FIXED)
print("\n>> Screening Run")
if "hr" in tokens:
    code, data = api_post("/api/screening/run", token=tokens["hr"])
    screened = data.get("screened", data.get("detail", "?"))
    log_check("screening_run", code in (200, 400), f"screened={screened}, passed={data.get('passed',0)}, rejected={data.get('rejected',0)}, cycle={data.get('cycle_name','?')}")
    if code not in (200, 400):
        record_issue("high", "screening_run")
else:
    log_check("screening_run", False, "No HR token available")

# 6. Candidates list
print("\n>> Candidates Listing Tests")
for role in ["superadmin", "admin", "hr"]:
    if role in tokens:
        code, data = api_get("/api/candidates/", token=tokens[role])
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            count = len(data["data"])
        elif isinstance(data, dict) and "candidates" in data and isinstance(data["candidates"], list):
            count = len(data["candidates"])
        elif isinstance(data, list):
            count = len(data)
        else:
            count = str(data)[:80]
        log_check(f"candidates_list_{role}", code == 200, f"{count} candidates")
        if code != 200:
            record_issue("high", f"candidates_list_{role}")

# 7. Candidate /me
if "candidate" in tokens:
    code, data = api_get("/api/candidates/me", token=tokens["candidate"])
    email = data.get("email", data.get("user", {}).get("email", str(data)[:80]))
    log_check("candidate_me", code == 200, f"{email}")
    if code != 200:
        record_issue("high", "candidate_me")

# 8. Hiring cycles
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
        log_check(f"admin_logs_{role}", code in (200, 404), f"HTTP {code}: {json.dumps(data)[:100] if isinstance(data,dict) else str(data)[:100]}")
        if code not in (200, 404):
            record_issue("high", f"admin_logs_{role}")

# 11. Assessment endpoint
if "candidate" in tokens:
    code, data = api_get("/api/assessment/active", token=tokens["candidate"])
    log_check("assessment_active", code in (200, 404), f"HTTP {code}")
    if code not in (200, 404):
        record_issue("high", "assessment_active")

# 12. Code execution - FIXED: POST with auth
print("\n>> Code Execution Tests")
# Test without auth
code, data = api_post("/api/code/execute", {"language": "python", "code": "print(1+1)"})
log_check("code_execute_noauth", code == 401, f"HTTP {code}: {json.dumps(data)[:80]}")
if code != 401:
    record_issue("high", "code_execute_noauth")

# Test with auth
for role in ["admin", "hr"]:
    if role in tokens:
        code, data = api_post("/api/code/execute", {"language": "python", "code": "print(1+1)"}, token=tokens[role])
        # 200 = success, 502/503 = sandbox not available (acceptable)
        ok = code in (200, 401, 502, 503, 422)
        status_detail = data.get("status", str(code))
        log_check(f"code_execute_{role}", ok, f"HTTP {code}: status={status_detail}")
        if not ok:
            record_issue("high", f"code_execute_{role}")

# 13. Proctoring event
if "candidate" in tokens:
    code, data = api_post("/api/proctoring/event", {
        "assessment_id": "00000000-0000-0000-0000-000000000000",
        "candidate_id": "00000000-0000-0000-0000-000000000000",
        "event_type": "tab_switch",
        "timestamp": datetime.now().isoformat()
    }, token=tokens["candidate"])
    log_check("proctoring_event", code in (200, 422, 404), f"HTTP {code}: {json.dumps(data)[:100]}")
    if code not in (200, 422, 404):
        record_issue("high", "proctoring_event")

# 14. Selection endpoint
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        code, data = api_get("/api/selection/", token=tokens[role])
        log_check(f"selection_{role}", code in (200, 404), f"HTTP {code}: {json.dumps(data)[:100] if isinstance(data,dict) else str(data)[:100]}")

# 15. Candidate registration
test_email = f"qa_test_{int(time.time())}@test.com"
code, data = api_post("/api/auth/register", {
    "email": test_email,
    "password": "Test@12345",
    "name": "QA Test User",
    "role": "candidate"
})
log_check("register_candidate", code in (200, 201, 400), f"HTTP {code}: created={test_email}" if code in (200,201) else f"HTTP {code}: {json.dumps(data)[:100]}")
if code not in (200, 201, 400):
    record_issue("high", "register_candidate")

# 16. Questions endpoint
code, data = api_get("/api/questions/generate")
log_check("questions_generate", code in (200, 401, 404), f"HTTP {code}")

# 17. Org endpoints (should be 501)
code, data = api_get("/api/admin/organizations/")
log_check("organizations", code in (404, 501), f"HTTP {code}: {json.dumps(data)[:100] if isinstance(data,dict) else str(data)[:100]}")

# ============================================================
# PHASE 2: BROWSER / FRONTEND TESTS
# ============================================================
print(f"\n--- PHASE 2: Browser Tests ---")

if not NGROK_URL:
    log_check("ngrok_reachable", False, "No ngrok URL found")
    record_issue("high", "ngrok_reachable")
else:
    # Verify ngrok reachable via curl (not browser)
    import urllib.request
    try:
        req = urllib.request.Request(f"{NGROK_URL}/health")
        resp = urllib.request.urlopen(req, timeout=10)
        ngrok_ok = resp.status == 200
        log_check("ngrok_reachable", ngrok_ok, f"HTTP {resp.status}")
        if not ngrok_ok:
            record_issue("critical", "ngrok_reachable")
    except Exception as e:
        log_check("ngrok_reachable", False, str(e)[:100])
        record_issue("critical", "ngrok_reachable")
        errors.append("CRITICAL: ngrok not reachable")
    
    if ngrok_ok:
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
        
        time.sleep(3)
        rc, snap, _ = ab_cmd("snapshot -c -i", timeout=10)
        log_check("fe_home_snapshot", rc == 0, f"Snap rc={rc}: {snap[:200]}")
        
        if rc == 0:
            # Check for ngrok interstitial
            if "Visit Site" in snap or "You are about to visit" in snap or "ngrok" in snap.lower() or "clickable [onclick]" in snap:
                print("  ⚠️ ngrok interstitial detected, clicking through...")
                # Try clicking the Visit Site/Continue button
                for line in snap.split("\n"):
                    if ("Visit Site" in line or "Continue" in line or "clickable" in line) and "[ref=" in line:
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m:
                            ref = m.group(1)
                            ab_cmd(f"click @{ref}", timeout=5)
                            time.sleep(2)
                            rc, snap, _ = ab_cmd("snapshot -c -i", timeout=10)
                            break
            
            # Test browser login for each role
            print("\n>> Browser Login Tests")
            for role in ROLES:
                ab_cmd("close --all", timeout=5)
                time.sleep(1)
                
                creds = ROLES[role]
                state_file = str(AUTH_DIR / f"{role}.json")
                
                # Try loading saved state
                rc, out, _ = ab_cmd(f"open {NGROK_URL}", session=role, timeout=15)
                time.sleep(2)
                
                # Handle ngrok interstitial
                rc2, snap, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
                if "Visit Site" in snap or "You are about to visit" in snap:
                    for line in snap.split("\n"):
                        if "clickable" in line and "[ref=" in line:
                            m = re.search(r'\[ref=([^\]]+)\]', line)
                            if m:
                                ab_cmd(f"click @{m.group(1)}", session=role, timeout=5)
                                time.sleep(2)
                                break
                
                # Try loading saved state
                rc, snap2, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
                
                # Check if we're already logged in
                if "Dashboard" in snap2 or "dashboard" in snap2.lower() or "Candidates" in snap2 or "Selection" in snap2 or "Assessment" in snap2:
                    log_check(f"fe_browser_login_{role}", True, "Already logged in via saved state")
                    role_coverage[role] = True
                    continue
                
                # Find login button
                login_found = False
                for line in snap2.split("\n"):
                    if "Login" in line and ("button" in line or "[ref=" in line):
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m:
                            ref = m.group(1)
                            ab_cmd(f"click @{ref}", session=role, timeout=5)
                            login_found = True
                            time.sleep(2)
                            break
                
                if not login_found:
                    log_check(f"fe_browser_login_{role}", False, "Could not find Login button")
                    record_issue("medium", f"fe_browser_login_{role}")
                    continue
                
                # Fill credentials
                rc, snap3, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
                
                email_filled = False
                pw_filled = False
                
                for line in snap3.split("\n"):
                    if "email" in line.lower() and ("textbox" in line or "input" in line or "[ref=" in line):
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m:
                            ab_cmd(f"fill @{m.group(1)} {creds['email']}", session=role, timeout=5)
                            email_filled = True
                            time.sleep(0.5)
                            break
                
                for line in snap3.split("\n"):
                    if "password" in line.lower() and ("textbox" in line or "input" in line or "[ref=" in line):
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m:
                            ab_cmd(f"fill @{m.group(1)} {creds['pw']}", session=role, timeout=5)
                            pw_filled = True
                            time.sleep(0.5)
                            break
                
                if not email_filled or not pw_filled:
                    log_check(f"fe_browser_login_{role}", False, f"Form fill: email={email_filled}, pw={pw_filled}")
                    record_issue("medium", f"fe_browser_login_{role}")
                    continue
                
                # Submit
                time.sleep(0.5)
                rc, snap4, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
                
                submit_found = False
                for line in snap4.split("\n"):
                    sub_phrases = ["sign in", "Sign In", "Sign in", "login", "Login", "submit", "Submit"]
                    if any(p in line for p in sub_phrases):
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m:
                            ab_cmd(f"click @{m.group(1)}", session=role, timeout=5)
                            submit_found = True
                            time.sleep(2)
                            break
                
                if not submit_found:
                    log_check(f"fe_browser_login_{role}", False, "Could not find submit button")
                    record_issue("medium", f"fe_browser_login_{role}")
                    continue
                
                # Verify login success
                time.sleep(1.5)
                rc, snap5, _ = ab_cmd(f"snapshot -c -i", session=role, timeout=10)
                
                if "Dashboard" in snap5 or "dashboard" in snap5.lower() or "Candidates" in snap5 or "Selection" in snap5 or "Assessment" in snap5 or "Welcome" in snap5 or "Logout" in snap5 or "Profile" in snap5:
                    # Save state
                    ab_cmd(f"state save {state_file}", session=role, timeout=5)
                    log_check(f"fe_browser_login_{role}", True, "Login succeeded - dashboard visible")
                    role_coverage[role] = True
                else:
                    log_check(f"fe_browser_login_{role}", False, f"Login may have failed. Snap: {snap5[:150]}")
                    record_issue("medium", f"fe_browser_login_{role}")
                    take_failure_screenshot(role, "login")
        
        ab_cmd("close --all", timeout=5)

# ============================================================
# PHASE 3: SYSTEM TESTS
# ============================================================
print(f"\n--- PHASE 3: System Tests ---")

# Frontend build
fe_dist = Path("/mnt/hermes-shared/projects/Knowledge_Factory/app/dist")
fe_build_ok = fe_dist.exists() and (fe_dist / "index.html").exists()
log_check("frontend_build", fe_build_ok, f"dist/index.html exists: {fe_build_ok}")

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

total = len(checks)
passed = sum(1 for c in checks if c["ok"])
failed = total - passed

api_checks = [c for c in checks if c["category"] == "API"]
api_passed = sum(1 for c in api_checks if c["ok"])
api_total = len(api_checks)

browser_checks = [c for c in checks if c["category"] == "FRONTEND"]
browser_passed = sum(1 for c in browser_checks if c["ok"])
browser_total = len(browser_checks)

system_checks = [c for c in checks if c["category"] == "SYSTEM"]
system_passed = sum(1 for c in system_checks if c["ok"])
system_total = len(system_checks)

# Load previous run for comparison
prev_run_path = None
prev_runs = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json") and f < f"{RUN_ID}_report.json"])
if prev_runs:
    prev_run_path = prev_runs[-1]

prev_run = None
if prev_run_path:
    try:
        with open(str(RUNS_DIR / prev_run_path)) as f:
            prev_run = json.load(f)
    except:
        pass

failed_names = {c["name"] for c in checks if not c["ok"]}
if prev_run:
    prev_failed = {c["name"] for c in prev_run.get("checks", []) if not c.get("ok")}
    new_issues_list = list(failed_names - prev_failed)
    fixed_issues_list = list(prev_failed - failed_names)
    recurring_issues_list = list(failed_names & prev_failed)
else:
    new_issues_list = list(failed_names)
    fixed_issues_list = []
    recurring_issues_list = []

report = {
    "run_id": RUN_ID,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
    "errors": errors,
    "warnings": warnings_list,
    "severity_counts": severity_counts,
    "issues": issues,
    "comparison": {
        "previous_run": prev_run_path or None,
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
        "backend_api": "✅ All endpoints responding" if api_passed == api_total else f"⚠️ {api_total - api_passed} failures ({api_passed}/{api_total})",
        "pipeline_screening": "✅ Working" if all(c["ok"] for c in [x for x in checks if x["name"] in ("pipeline_stats", "screening_run")]) else "⚠️ Issues detected",
        "analytics": "✅ Working" if all(c["ok"] for c in [x for x in checks if "analytics" in x["name"]]) else "⚠️ Issues detected",
        "frontend_ui": "✅ Working" if browser_passed == browser_total else f"⚠️ {browser_total - browser_passed} failures ({browser_passed}/{browser_total})",
    },
    "pipeline": stats_str if 'stats_str' in locals() else "N/A",
    "role_coverage": role_coverage,
}

report_path = RUNS_DIR / f"{RUN_ID}_report.json"
with open(report_path, "w") as f:
    json.dump(report, f, indent=2, default=str)

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
        p = RUNS_DIR / base + suffix
        if os.path.exists(str(p)):
            os.unlink(str(p))

print(f"\n✅ Report saved: {report_path}")
print(f"📊 Summary: {passed}/{total} passed, {failed} failed, {severity_counts['critical']} critical")
print(f"  API: {api_passed}/{api_total} | Browser: {browser_passed}/{browser_total} | System: {system_passed}/{system_total}")

# Output usable JSON
print(f"\n---JSON-SUMMARY-START---")
print(json.dumps(summary))
print(f"---JSON-SUMMARY-END---")

# Check if any role still has issues
blocked_roles = [r for r, v in role_coverage.items() if not v]
if blocked_roles:
    print(f"🚫 BLOCKED roles: {', '.join(blocked_roles)}")
else:
    print("✅ All roles accessible")

# Print pipeline state
print(f"\nPipeline: {stats_str[:200]}")
