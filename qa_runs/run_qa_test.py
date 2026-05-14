#!/usr/bin/env python3
"""
Knowledge Factory Autonomous QA Tester
Runs comprehensive end-to-end tests against the live application.
Combines API-level checks with browser-based E2E testing via agent-browser CLI.

Usage: python3 run_qa_test.py
"""
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
NGROK_URL = os.environ.get("NGROK_URL", "https://ila-sturdiest-oversentimentally.ngrok-free.dev")

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
PROJECT_ROOT = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory")
AUTH_DIR = PROJECT_ROOT / "auth"
FAILURES_DIR = PROJECT_ROOT / "failures"
QA_RUNS_DIR = PROJECT_ROOT / "qa_runs"
BASELINES_DIR = PROJECT_ROOT / "baselines"

AB = "/opt/hermes_shared_memory/bin/ab"

os.makedirs(AUTH_DIR, exist_ok=True)
os.makedirs(FAILURES_DIR / RUN_ID, exist_ok=True)
os.makedirs(QA_RUNS_DIR, exist_ok=True)
os.makedirs(BASELINES_DIR, exist_ok=True)

# ─── Credentials ───────────────────────────────────────────────────────────
CREDENTIALS = {
    "superadmin": {
        "email": "superadmin@knowledgefactory.io",
        "password": "Super@12345",
        "role": "SUPERADMIN",
    },
    "admin": {
        "email": "admin@knowledgefactory.io",
        "password": "admin123",
        "role": "ADMIN",
    },
    "hr": {
        "email": "hr@test.com",
        "password": "Hr@12345",
        "role": "HR",
    },
    "interviewer": {
        "email": "interviewer@test.com",
        "password": "Interviewer@12345",
        "role": "INTERVIEWER",
    },
    "candidate": {
        "email": "candidate@test.com",
        "password": "Candidate@12345",
        "role": "CANDIDATE",
    },
}

CANDIDATE_CREDENTIALS = {
    "alice": {"email": "alice@test.com", "password": "Candidate@12345"},
    "bob": {"email": "bob@test.com", "password": "Candidate@12345"},
    "charlie": {"email": "charlie@test.com", "password": "Candidate@12345"},
    "divya": {"email": "divya@test.com", "password": "Candidate@12345"},
    "esha": {"email": "esha@test.com", "password": "Candidate@12345"},
}

# ─── Test Results ──────────────────────────────────────────────────────────
results = {
    "run_id": RUN_ID,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "passed": [],
    "failed": [],
    "warnings": [],
    "critical": [],
}

def mark(level, desc, detail=None):
    entry = {"desc": desc, "detail": detail} if detail else {"desc": desc}
    results[level].append(entry)
    icon = {"passed": "✅", "failed": "❌", "warnings": "⚠️", "critical": "🔴"}.get(level, "❓")
    print(f"  {icon} [{level.upper()}] {desc}")
    if detail:
        print(f"     └─ {detail}")

def run_ab(args, timeout=30):
    """Run agent-browser CLI and return (returncode, stdout, stderr)."""
    cmd = [AB] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def api_get(path, token=None, expected_status=200):
    """Make GET request and return parsed JSON."""
    import urllib.request
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode()
            status = resp.status
            return status, json.loads(data) if data else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else "{}"
        try:
            return e.code, json.loads(body)
        except:
            return e.code, {"detail": body}
    except Exception as e:
        return 0, {"error": str(e)}

def api_post(path, body, token=None, expected_status=200):
    import urllib.request
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else "{}"
        try:
            return e.code, json.loads(body)
        except:
            return e.code, {"detail": body}
    except Exception as e:
        return 0, {"error": str(e)}

def api_patch(path, body, token=None):
    import urllib.request
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="PATCH")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else "{}"
        try:
            return e.code, json.loads(body)
        except:
            return e.code, {"detail": body}
    except Exception as e:
        return 0, {"error": str(e)}

def login(email, password):
    """Login and return token."""
    status, data = api_post("/api/auth/login", {"email": email, "password": password})
    if status == 200 and "access_token" in data:
        return data["access_token"], data
    return None, data

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════
def test_health():
    print("\n═══════ SECTION 1: Health Check ═══════")
    try:
        status, data = api_get("/health")
        if status == 200 and data.get("status") == "ok":
            mark("passed", "Health check: GET /health returns 200 OK")
        else:
            mark("critical", f"Health check FAILED: status={status}, data={data}")
            return False
    except Exception as e:
        mark("critical", f"Health check EXCEPTION: {e}")
        return False
    return True

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: AUTH TESTING (API level)
# ═══════════════════════════════════════════════════════════════════════════
def test_auth():
    print("\n═══════ SECTION 2: Authentication ═══════")
    tokens = {}
    
    for role_name, creds in CREDENTIALS.items():
        token, data = login(creds["email"], creds["password"])
        if token:
            tokens[role_name] = token
            mark("passed", f"Login: {role_name} ({creds['email']}) — role={data.get('role', '?')}")
        else:
            mark("critical", f"Login FAILED: {role_name} ({creds['email']}) — {data}")
    
    # Also test candidate accounts
    for name, creds in CANDIDATE_CREDENTIALS.items():
        token, data = login(creds["email"], creds["password"])
        if token:
            tokens[f"candidate_{name}"] = token
            mark("passed", f"Login: {name} ({creds['email']})")
        else:
            mark("warning", f"Login FAILED: {name} ({creds['email']}) — {data}")
    
    # Verify /me endpoint for each role
    for role_name in ["superadmin", "admin", "hr", "interviewer", "candidate"]:
        if role_name in tokens:
            status, data = api_get("/api/auth/me", token=tokens[role_name])
            if status == 200:
                mark("passed", f"/me OK: {role_name} (role={data.get('role', '?')})")
            else:
                mark("failed", f"/me FAILED: {role_name} — status={status}")
    
    return tokens

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: CANDIDATES API
# ═══════════════════════════════════════════════════════════════════════════
def test_candidates(tokens):
    print("\n═══════ SECTION 3: Candidates API ═══════")
    
    for role in ["admin", "hr"]:
        if role in tokens:
            status, data = api_get("/api/candidates/", token=tokens[role])
            if status == 200:
                candidates = data.get("data") or data.get("candidates") or data or []
                if isinstance(candidates, list):
                    count = len(candidates)
                    mark("passed", f"Candidates list ({role}): {count} candidates")
                else:
                    mark("passed", f"Candidates list ({role}): OK (data format: {type(candidates).__name__})")
            else:
                mark("failed", f"Candidates list ({role}): status={status}")
    
    # Candidate /me
    if "candidate" in tokens:
        status, data = api_get("/api/candidates/me", token=tokens["candidate"])
        if status == 200:
            mark("passed", "Candidate /me: OK")
        else:
            mark("failed", f"Candidate /me: status={status}")
    
    for name in ["alice", "bob", "charlie", "divya", "esha"]:
        key = f"candidate_{name}"
        if key in tokens:
            status, data = api_get("/api/candidates/me", token=tokens[key])
            if status == 200:
                mark("passed", f"Candidate ({name}): /candidates/me OK")
            else:
                mark("warning", f"Candidate ({name}): /candidates/me — status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: SCREENING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════
def test_screening(tokens):
    print("\n═══════ SECTION 4: Screening Pipeline ═══════")
    
    # Pipeline stats
    status, data = api_get("/api/screening/pipeline-stats")
    if status == 200:
        stats = data.get("stats") or data
        status_count = len(stats) if isinstance(stats, dict) else "OK"
        mark("passed", f"Pipeline stats: {status_count} statuses")
    else:
        mark("warning", f"Pipeline stats: status={status}")
    
    # Screening run
    if "hr" in tokens:
        status, data = api_post("/api/screening/run", {}, token=tokens["hr"])
        if status == 200:
            mark("passed", f"Screening run: OK — {json.dumps(data)[:100]}")
        else:
            mark("warning", f"Screening run: status={status} — {str(data)[:100]}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════
def test_analytics(tokens):
    print("\n═══════ SECTION 5: Analytics ═══════")
    
    if "admin" in tokens:
        status, data = api_get("/api/analytics/funnel", token=tokens["admin"])
        if status == 200:
            mark("passed", "Analytics Funnel: OK")
        else:
            mark("warning", f"Analytics Funnel: status={status}")
        
        status, data = api_get("/api/analytics/dashboard", token=tokens["admin"])
        if status == 200:
            mark("passed", "Analytics Dashboard: OK")
        else:
            mark("warning", f"Analytics Dashboard: status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: HIRING CYCLES
# ═══════════════════════════════════════════════════════════════════════════
def test_hiring_cycles(tokens):
    print("\n═══════ SECTION 6: Hiring Cycles ═══════")
    
    if "admin" in tokens:
        status, data = api_get("/api/hiring-cycles/", token=tokens["admin"])
        if status == 200:
            cycles = data if isinstance(data, list) else data.get("data") or data.get("cycles") or []
            count = len(cycles)
            mark("passed", f"Hiring cycles: {count} cycles")
        else:
            mark("warning", f"Hiring cycles: status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: REGISTRATION (new candidate)
# ═══════════════════════════════════════════════════════════════════════════
def test_registration():
    print("\n═══════ SECTION 7: Registration ═══════")
    
    ts = int(time.time())
    email = f"qa_test_{ts}@test.com"
    reg_data = {
        "email": email,
        "password": "QaTest@12345",
        "full_name": f"QA Test User {ts % 100000}",
        "role": "candidate",
        "phone": f"+9112345{ts % 100000:05d}",
        "college": "QA Test University",
        "branch": "CSE",
        "cgpa": 8.5,
        "passed_out_year": 2026,
    }
    
    status, data = api_post("/api/auth/register", reg_data)
    if status in (200, 201):
        mark("passed", f"Registration: {email} — OK")
    else:
        # Could already exist or other error
        mark("warning", f"Registration: {email} — status={status}, detail={str(data)[:100]}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: ADMIN ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════
def test_admin(tokens):
    print("\n═══════ SECTION 8: Admin ═══════")
    
    if "admin" in tokens:
        status, data = api_get("/api/admin/users", token=tokens["admin"])
        if status == 200:
            mark("passed", "Admin Users: OK")
        else:
            mark("warning", f"Admin Users: status={status}")
        
        status, data = api_get("/api/admin/logs", token=tokens["admin"])
        if status == 200:
            mark("passed", "Admin Logs: OK")
        else:
            mark("warning", f"Admin Logs: status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: BROWSER-BASED E2E TESTS
# ═══════════════════════════════════════════════════════════════════════════
def test_browser_e2e():
    """
    Use agent-browser CLI to test the frontend UI.
    Tests: login flow, navigation, page loads for each role.
    """
    print("\n═══════ SECTION 9: Browser E2E Tests ═══════")
    
    # First, close any existing sessions
    rc, out, err = run_ab(["close", "--all"])
    print(f"  Close all sessions: rc={rc}")
    
    for role_name, creds in CREDENTIALS.items():
        print(f"\n  ── Testing role: {role_name} ({creds['email']}) ──")
        
        # Check if saved auth state exists
        auth_file = AUTH_DIR / f"{role_name}.json"
        
        if auth_file.exists():
            # Load saved state and navigate directly
            rc, out, err = run_ab([
                "--session", role_name,
                "--state", str(auth_file),
                "open", NGROK_URL,
            ])
            print(f"    Load state: rc={rc}")
            if rc != 0:
                mark("warning", f"Browser ({role_name}): saved state failed, will re-login")
                auth_file.unlink(missing_ok=True)
                rc2, out2, err2 = run_ab(["--session", role_name, "open", NGROK_URL])
                print(f"    Fresh open: rc={rc2}")
        else:
            # Fresh login
            rc, out, err = run_ab(["--session", role_name, "open", NGROK_URL])
            print(f"    Open URL: rc={rc}")
        
        if rc != 0:
            mark("failed", f"Browser ({role_name}): failed to open page")
            # Screenshot
            run_ab(["--session", role_name, "screenshot",
                    str(FAILURES_DIR / RUN_ID / f"{role_name}_open_fail.png")])
            continue
        
        time.sleep(2)
        
        # Take snapshot to see what's on the page
        rc, out, err = run_ab(["--session", role_name, "snapshot", "-c", "-i"])
        if rc == 0 and out:
            print(f"    Snapshot: {len(out)} chars")
        
        # Check if we need to login (look for login button/email field)
        # The SPA should show login page first
        rc, out, err = run_ab(["--session", role_name, "eval",
                               "document.querySelector('input[type=email], input[name=email], input[placeholder*=email]') !== null"])
        has_email_field = rc == 0 and out and "true" in out.lower()
        
        if has_email_field:
            print(f"    Login page detected, performing login...")
            
            # Find and fill email field
            rc, out, err = run_ab(["--session", role_name, "eval",
                                   f"(function(){{ let el = document.querySelector('input[type=email], input[name=email], input[placeholder*=email]'); if(el) {{ el.value='{creds['email']}'; el.dispatchEvent(new Event('input', {{bubbles:true}})); return 'filled'; }} return 'not found'; }})()"])
            print(f"    Fill email: rc={rc}, out={out}")
            
            # Find and fill password field
            rc, out, err = run_ab(["--session", role_name, "eval",
                                   f"(function(){{ let el = document.querySelector('input[type=password], input[name=password], input[placeholder*=password]'); if(el) {{ el.value='{creds['password']}'; el.dispatchEvent(new Event('input', {{bubbles:true}})); return 'filled'; }} return 'not found'; }})()"])
            print(f"    Fill password: rc={rc}, out={out}")
            
            time.sleep(0.5)
            
            # Try clicking the submit button
            rc, out, err = run_ab(["--session", role_name, "eval",
                                   "(function(){ let btn = document.querySelector('button[type=submit], button:contains(Sign In), button:contains(Login), button:contains(Log in)'); if(btn) { btn.click(); return 'clicked'; } return 'not found'; })()"])
            print(f"    Click submit: rc={rc}, out={out}")
            
            # Also try via variations
            if "not found" in (out or ""):
                rc, out, err = run_ab(["--session", role_name, "eval",
                                       "document.querySelector('form button').click(); 'clicked form button'"])
                print(f"    Click form button: rc={rc}, out={out}")
            
            time.sleep(3)
        
        # Save auth state
        rc, out, err = run_ab(["--session", role_name, "state", "save", str(auth_file)])
        print(f"    Save state: rc={rc}")
        
        # Take a screenshot after login attempt
        rc, out, err = run_ab(["--session", role_name, "screenshot",
                               str(FAILURES_DIR / RUN_ID / f"{role_name}_after_login.png")])
        
        # Check for errors in console
        rc, out, err = run_ab(["--session", role_name, "console", "--json"])
        if out and "error" in out.lower():
            mark("warning", f"Browser ({role_name}): console errors detected",
                 out[:200])
        
        # Try to navigate - get snapshot after login
        rc, out, err = run_ab(["--session", role_name, "snapshot", "-c", "-i"])
        if rc == 0 and out:
            print(f"    Post-login snapshot: {len(out)} chars")
            # Save baseline
            baseline_file = BASELINES_DIR / f"{role_name}_dashboard.txt"
            with open(baseline_file, "w") as f:
                f.write(out)
        
        # Try clicking dashboard/home link
        rc, out, err = run_ab(["--session", role_name, "eval",
                               "document.title"])
        print(f"    Page title: {out}")
        
        # Check for 404 or 500 network errors
        rc, out, err = run_ab(["--session", role_name, "network", "requests", "--status", "4xx,5xx"])
        if out and out.strip():
            mark("warning", f"Browser ({role_name}): network errors", out[:200])
    
    # Close all sessions
    run_ab(["close", "--all"])
    print("  Browser sessions closed.")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10: KF-SPECIFIC TESTS
# ═══════════════════════════════════════════════════════════════════════════
def test_kf_specific(tokens):
    print("\n═══════ SECTION 10: KF-Specific Tests ═══════")
    
    # Questions endpoint
    status, data = api_get("/api/questions/")
    mark("passed" if status != 500 else "warning", f"Questions list: {status}")
    
    # Code execution endpoint
    status, data = api_get("/api/code/")
    mark("passed" if status != 500 else "warning", f"Code execution: {status}")
    
    # Proctoring event (POST with empty should give 422, not 500)
    if "admin" in tokens:
        status, data = api_post("/api/proctoring/event", {}, token=tokens["admin"])
        if status == 422:
            mark("passed", "Proctoring event: 422 (schema validation as expected)")
        else:
            mark("warning", f"Proctoring event: status={status} (expected 422)")
    
    # Assessment endpoints
    status, data = api_get("/api/assessment/")
    if status != 500:
        mark("passed", f"Assessment list: {status}")
    else:
        mark("warning", f"Assessment list: {status}")
    
    # Selection endpoint
    if "admin" in tokens:
        status, data = api_post("/api/selection/bulk-select", {"candidate_ids": []}, token=tokens["admin"])
        if status in (200, 422):
            mark("passed", f"Selection bulk-select: {status} (expected 422 for empty list)")
        else:
            mark("warning", f"Selection bulk-select: {status}")
    
    # Interview feedback
    if "interviewer" in tokens and "candidate" in tokens:
        status, data = api_get("/api/candidates/me/feedback", token=tokens["candidate"])
        if status == 200:
            mark("passed", "Interview feedback (candidate): OK")
        else:
            mark("warning", f"Interview feedback (candidate): status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print(f"╔══════════════════════════════════════════════════════════╗")
    print(f"║   Knowledge Factory QA Run #{RUN_ID}            ║")
    print(f"║   Target: {BASE_URL}")
    print(f"║   NGROK:  {NGROK_URL}")
    print(f"╚══════════════════════════════════════════════════════════╝")
    print(f"Started: {datetime.now().isoformat()}")
    
    start_time = time.time()
    
    # Section 1: Health
    if not test_health():
        mark("critical", "Health check failed — aborting")
        save_results()
        return
    
    # Section 2: Auth
    tokens = test_auth()
    
    if not tokens:
        mark("critical", "No tokens obtained — cannot continue API tests")
    else:
        # Section 3-10: All API tests
        test_candidates(tokens)
        test_screening(tokens)
        test_analytics(tokens)
        test_hiring_cycles(tokens)
        test_registration()
        test_admin(tokens)
        test_kf_specific(tokens)
    
    # Section 9: Browser E2E (always run if health check passes)
    test_browser_e2e()
    
    elapsed = time.time() - start_time
    print(f"\n{'═' * 60}")
    print(f"Completed in {elapsed:.1f}s")
    
    # Summary
    passed = len(results["passed"])
    failed = len(results["failed"])
    warnings = len(results["warnings"])
    critical = len(results["critical"])
    total = passed + failed + warnings + critical
    
    print(f"\n{'═' * 60}")
    print(f"  RESULTS: ✅ {passed} passed | ❌ {failed} failed | ⚠️  {warnings} warnings | 🔴 {critical} critical")
    print(f"  Total: {total} checks")
    print(f"{'═' * 60}")
    
    # Save results
    save_results()
    
    # Timeout check
    if elapsed > 1800:  # 30 minutes
        results["critical"].append({"desc": "TIMEOUT: Run exceeded 30 minutes", "detail": f"took {elapsed:.0f}s"})
        mark("critical", f"TIMEOUT: Run exceeded 30 minutes ({elapsed:.0f}s)")

def save_results():
    run_file = QA_RUNS_DIR / f"{RUN_ID}.json"
    with open(run_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved: {run_file}")
    
    # Cleanup old runs (keep last 10)
    runs = sorted(QA_RUNS_DIR.glob("*.json"), key=os.path.getmtime)
    for old in runs[:-10]:
        old.unlink()
        print(f"  Removed old run: {old.name}")

if __name__ == "__main__":
    main()
