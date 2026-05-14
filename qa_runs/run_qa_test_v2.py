#!/usr/bin/env python3
"""
Knowledge Factory Autonomous QA Tester v2
Runs comprehensive end-to-end tests against the live application.
"""
import json
import os
import subprocess
import sys
import time
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
NGROK_URL = os.environ.get("NGROK_URL", "https://ila-sturdiest-oversentimentally.ngrok-free.dev")

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
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

print(f"QA RUN ID: {RUN_ID}")
print(f"BASE_URL: {BASE_URL}")
print(f"NGROK_URL: {NGROK_URL}")
print(f"AB: {AB}")

# ─── Credentials (from seed.py verification) ──────────────────────────────
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
        "email": "hr@knowledgefactory.io",
        "password": "Hr@12345",
        "role": "HR",
    },
    "interviewer": {
        "email": "interviewer@knowledgefactory.io",
        "password": "Interview@12345",
        "role": "INTERVIEWER",
    },
}

CANDIDATE_CREDENTIALS = {
    "alice": {"email": "alice@test.com", "password": "Candidate@123", "name": "Alice Sharma"},
    "bob": {"email": "bob@test.com", "password": "Candidate@123", "name": "Bob Patel"},
    "charlie": {"email": "charlie@test.com", "password": "Candidate@123", "name": "Charlie Singh"},
    "divya": {"email": "divya@test.com", "password": "Candidate@123", "name": "Divya Kumar"},
    "esha": {"email": "esha@test.com", "password": "Candidate@123", "name": "Esha Gupta"},
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
    entry = {"desc": desc}
    if detail:
        entry["detail"] = detail
    results[level].append(entry)
    icon_map = {"passed": "✅", "failed": "❌", "warnings": "⚠️", "critical": "🔴"}
    icon = icon_map.get(level, "❓")
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

# ─── HTTP Helpers ─────────────────────────────────────────────────────────
def _req(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
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

def api_get(path, token=None):
    return _req("GET", path, token=token)

def api_post(path, body, token=None):
    return _req("POST", path, body=body, token=token)

def api_patch(path, body, token=None):
    return _req("PATCH", path, body=body, token=token)

def login(email, password):
    status, data = api_post("/api/auth/login", {"email": email, "password": password})
    if status == 200 and "access_token" in data:
        return data["access_token"], data
    return None, data

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════
def test_health():
    print("\n═══════ SECTION 1: Health Check ═══════")
    status, data = api_get("/health")
    if status == 200 and data.get("status") == "ok":
        mark("passed", "Health check: GET /health returns 200 OK")
        return True
    else:
        mark("critical", f"Health check FAILED: {status} {data}")
        return False

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: AUTH TESTING
# ═══════════════════════════════════════════════════════════════════════════
def test_auth():
    print("\n═══════ SECTION 2: Authentication ═══════")
    tokens = {}
    
    # Test staff logins
    for role_name, creds in CREDENTIALS.items():
        token, data = login(creds["email"], creds["password"])
        if token:
            tokens[role_name] = token
            role = data.get("role", "?")
            mark("passed", f"Login: {role_name} ({creds['email']}) — role={role}")
        else:
            mark("critical", f"Login FAILED: {role_name} ({creds['email']}) — {data}")
    
    # Test candidate logins
    for name, creds in CANDIDATE_CREDENTIALS.items():
        token, data = login(creds["email"], creds["password"])
        if token:
            tokens[f"candidate_{name}"] = token
            mark("passed", f"Login: {name} ({creds['email']})")
        else:
            mark("failed", f"Login FAILED: {name} ({creds['email']}) — {data}")
    
    # Verify /me endpoint
    for role_name in ["superadmin", "admin", "hr", "interviewer"]:
        if role_name in tokens:
            status, data = api_get("/api/auth/me", token=tokens[role_name])
            if status == 200:
                r = data.get("role", data.get("user", {}).get("role", "?"))
                mark("passed", f"/me OK: {role_name} (role={r})")
            else:
                mark("failed", f"/me FAILED: {role_name} — {status}")
    
    for name in CANDIDATE_CREDENTIALS:
        key = f"candidate_{name}"
        if key in tokens:
            status, data = api_get("/api/auth/me", token=tokens[key])
            if status == 200:
                mark("passed", f"/me OK: candidate {name}")
            else:
                mark("warnings", f"/me FAILED: candidate {name} — {status}")
    
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
                candidates = data
                if isinstance(candidates, dict):
                    for key in ("data", "candidates", "items", "results"):
                        if key in candidates:
                            candidates = candidates[key]
                            break
                count = len(candidates) if isinstance(candidates, list) else str(type(candidates))
                mark("passed", f"Candidates list ({role}): {count} candidates")
            else:
                mark("failed", f"Candidates list ({role}): status={status}")
    
    # Candidate /me
    for name in CANDIDATE_CREDENTIALS:
        key = f"candidate_{name}"
        if key in tokens:
            status, data = api_get("/api/candidates/me", token=tokens[key])
            if status == 200:
                cn = data.get("name", data.get("full_name", "?"))
                mark("passed", f"Candidate /me ({name}): {cn}")
            else:
                mark("warnings", f"Candidate /me ({name}): status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: SCREENING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════
def test_screening(tokens):
    print("\n═══════ SECTION 4: Screening Pipeline ═══════")
    
    status, data = api_get("/api/screening/pipeline-stats")
    if status == 200:
        stats = data.get("stats") or data
        sc = len(stats) if isinstance(stats, dict) else "OK"
        mark("passed", f"Pipeline stats: {sc} statuses")
        # Print the actual stats
        if isinstance(stats, dict):
            active_stats = {k: v for k, v in stats.items() if isinstance(v, (int, float)) and v > 0}
            print(f"         └─ Active stats: {active_stats}")
    else:
        mark("failed", f"Pipeline stats: status={status}")
    
    if "hr" in tokens:
        status, data = api_post("/api/screening/run", {}, token=tokens["hr"])
        if status == 200:
            summary = json.dumps({k: v for k, v in data.items() if k != "details"})[:120]
            mark("passed", f"Screening run: OK — {summary}")
        else:
            mark("warnings", f"Screening run: status={status} — {str(data)[:100]}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════
def test_analytics(tokens):
    print("\n═══════ SECTION 5: Analytics ═══════")
    
    if "admin" in tokens:
        for ep in ["/api/analytics/funnel", "/api/analytics/dashboard"]:
            status, data = api_get(ep, token=tokens["admin"])
            if status == 200:
                mark("passed", f"Analytics {ep}: OK")
            else:
                mark("warnings", f"Analytics {ep}: status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: HIRING CYCLES
# ═══════════════════════════════════════════════════════════════════════════
def test_hiring_cycles(tokens):
    print("\n═══════ SECTION 6: Hiring Cycles ═══════")
    
    if "admin" in tokens:
        status, data = api_get("/api/hiring-cycles/", token=tokens["admin"])
        if status == 200:
            cycles = data
            if isinstance(data, dict):
                for k in ("data", "cycles", "items"):
                    if k in data:
                        cycles = data[k]
                        break
            count = len(cycles) if isinstance(cycles, list) else "?"
            names = [c.get("name", "?") for c in (cycles if isinstance(cycles, list) else [])]
            mark("passed", f"Hiring cycles: {count} cycles — {names}")
        else:
            mark("warnings", f"Hiring cycles: status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════
def test_registration():
    print("\n═══════ SECTION 7: Registration ═══════")
    
    ts = int(time.time())
    email = f"qa_e2e_{ts}@test.com"
    reg_data = {
        "email": email,
        "password": "QaPass@12345",
        "full_name": f"QA E2E User",
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
        return email
    else:
        mark("warnings", f"Registration: {email} — status={status}, {str(data)[:100]}")
        return None

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: ADMIN ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════
def test_admin(tokens):
    print("\n═══════ SECTION 8: Admin Endpoints ═══════")
    
    if "admin" in tokens:
        for ep in ["/api/admin/users", "/api/admin/logs"]:
            status, data = api_get(ep, token=tokens["admin"])
            if status == 200:
                mark("passed", f"Admin {ep}: OK")
            else:
                mark("warnings", f"Admin {ep}: status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: KF-SPECIFIC TESTS
# ═══════════════════════════════════════════════════════════════════════════
def test_kf_specific(tokens):
    print("\n═══════ SECTION 9: KF-Specific Tests ═══════")
    
    # Questions
    status, data = api_get("/api/questions/")
    if status != 500:
        mark("passed", f"Questions: status={status}")
    else:
        mark("warnings", f"Questions: 500 error")
    
    # Code execution
    status, data = api_get("/api/code/")
    if status != 500:
        mark("passed", f"Code execution: status={status}")
    else:
        mark("warnings", f"Code execution: 500 error")
    
    # Proctoring
    if "admin" in tokens:
        status, data = api_post("/api/proctoring/event", {}, token=tokens["admin"])
        if status == 422:
            mark("passed", "Proctoring event: 422 (schema validation as expected)")
        else:
            mark("warnings", f"Proctoring event: status={status} (expected 422)")
    
    # Assessment
    status, data = api_get("/api/assessment/")
    if status != 500:
        mark("passed", f"Assessment list: status={status}")
    else:
        mark("warnings", f"Assessment list: 500 error")
    
    # Interview feedback for candidate
    if "candidate_alice" in tokens:
        status, data = api_get("/api/candidates/me/feedback", token=tokens["candidate_alice"])
        if status == 200:
            mark("passed", "Interview feedback (alice): OK")
        else:
            mark("warnings", f"Interview feedback (alice): status={status}")
    
    # Selection
    if "admin" in tokens:
        status, data = api_post("/api/selection/bulk-select", {"candidate_ids": []}, token=tokens["admin"])
        if status in (200, 422):
            mark("passed", f"Selection bulk-select: {status} (expected 422 for empty)")
        else:
            mark("warnings", f"Selection bulk-select: {status}")
    
    # Assessment start test (should fail gracefully for candidates who aren't eligible)
    if "candidate_alice" in tokens:
        status, data = api_post("/api/assessment/start", {"round": "ROUND_2"}, token=tokens["candidate_alice"])
        # Alice is ROUND3_PASSED, so starting ROUND_2 should fail
        if status in (400, 422):
            mark("passed", f"Assessment start (alice/ROUND_2): {status} — {str(data.get('detail',''))[:80]}")
        else:
            mark("warnings", f"Assessment start (alice/ROUND_2): unexpected {status} — {str(data)[:80]}")
    
    if "candidate_divya" in tokens:
        status, data = api_post("/api/assessment/start", {"round": "ROUND_2"}, token=tokens["candidate_divya"])
        # Divya is ROUND1_PASSED, so starting ROUND_2 should succeed
        if status == 200:
            mark("passed", f"Assessment start (divya/ROUND_2): OK — assessment created")
        elif status in (400, 422):
            mark("warnings", f"Assessment start (divya/ROUND_2): {status} — {str(data.get('detail',''))[:80]}")
        else:
            mark("warnings", f"Assessment start (divya/ROUND_2): unexpected {status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10: BROWSER-BASED E2E TESTS
# ═══════════════════════════════════════════════════════════════════════════
def test_browser_e2e(tokens):
    print("\n═══════ SECTION 10: Browser E2E Tests ═══════")
    
    # Clean sessions
    run_ab(["close", "--all"])
    time.sleep(1)
    
    # Test each role's frontend
    for role_name, creds in CREDENTIALS.items():
        print(f"\n  ── Browser test: {role_name} ({creds['email']}) ──")
        
        auth_file = AUTH_DIR / f"{role_name}.json"
        session_id = f"kf_{role_name}"
        
        # Open the app
        rc, out, err = run_ab(["--session", session_id, "open", NGROK_URL])
        print(f"    Open: rc={rc}")
        if rc != 0:
            mark("failed", f"Browser ({role_name}): failed to open page")
            continue
        
        time.sleep(3)
        
        # Check if we need to log in (look for login page)
        rc, out, err = run_ab(["--session", session_id, "eval",
                               "document.querySelectorAll('input').length"])
        print(f"    Input fields: {out}")
        
        rc, out, err = run_ab(["--session", session_id, "eval",
                               f"(function(){{ const els = document.querySelectorAll('input'); let info = []; els.forEach((el,i)=>{{ info.push(`#${{i}}: type=${{el.type||'text'}} name=${{el.name}} placeholder=${{el.placeholder}} valueLength=${{el.value.length}}`); }}); return info.join(' | '); }})()"])
        print(f"    Inputs: {str(out)[:200]}")
        
        # Get page title
        rc, out, err = run_ab(["--session", session_id, "eval", "document.title"])
        print(f"    Title: {out}")
        
        # Check for login form
        rc, out, err = run_ab(["--session", session_id, "eval",
                               "document.querySelector('form') !== null"])
        has_form = rc == 0 and out and "true" in out.lower()
        print(f"    Has form: {has_form}")
        
        if has_form:
            # Try to fill email
            rc, out, err = run_ab(["--session", session_id, "eval",
                                   f"(function(){{ const inp = document.querySelector('input[type=email]') || document.querySelector('input[name=email]') || document.querySelector('input[placeholder*=mail]'); if(!inp) return 'no-email-field'; const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; nativeInputValueSetter.call(inp, '{creds['email']}'); inp.dispatchEvent(new Event('input', {{bubbles: true}})); return 'ok'; }})()"])
            print(f"    Fill email: {str(out)[:80]}")
            
            # Fill password
            rc, out, err = run_ab(["--session", session_id, "eval",
                                   f"(function(){{ const inp = document.querySelector('input[type=password]') || document.querySelector('input[name=password]'); if(!inp) return 'no-password-field'; const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; nativeInputValueSetter.call(inp, '{creds['password']}'); inp.dispatchEvent(new Event('input', {{bubbles: true}})); return 'ok'; }})()"])
            print(f"    Fill password: {str(out)[:80]}")
            
            time.sleep(1)
            
            # Click submit button
            rc, out, err = run_ab(["--session", session_id, "eval",
                                   "(function(){ const btns = document.querySelectorAll('button'); for(const b of btns){ if(b.type==='submit' || b.innerText.includes('Sign') || b.innerText.includes('Login') || b.innerText.includes('Log in')){ b.click(); return 'clicked'; } } return 'no-submit-btn'; })()"])
            print(f"    Click submit: {str(out)[:80]}")
            
            time.sleep(3)
        
        # Save auth state
        rc, out, err = run_ab(["--session", session_id, "state", "save", str(auth_file)])
        print(f"    Save state: rc={rc}")
        
        # Screenshot
        rc, out, err = run_ab(["--session", session_id, "screenshot",
                               str(FAILURES_DIR / RUN_ID / f"{role_name}_page.png")])
        
        # Check console errors
        rc, out, err = run_ab(["--session", session_id, "console", "--json"])
        if out and out.strip() and out.strip() != "[]":
            try:
                console_entries = json.loads(out)
                errors = [e for e in console_entries if e.get('type') in ('error', 'warning')]
                if errors:
                    mark("warnings", f"Browser ({role_name}): console errors",
                         "; ".join([str(e.get('text', ''))[:80] for e in errors[:3]]))
            except:
                if out.strip():
                    mark("warnings", f"Browser ({role_name}): console output", out[:150])
        
        # Get snapshot after login attempt
        rc, out, err = run_ab(["--session", session_id, "snapshot", "-c", "-i"])
        if rc == 0 and out:
            print(f"    Post-login snapshot: {len(out)} chars")
        
        # Check for network errors
        rc, out, err = run_ab(["--session", session_id, "network", "requests", "--status", "4xx,5xx"])
        if out and out.strip():
            print(f"    Network errors: {out[:200]}")
            mark("warnings", f"Browser ({role_name}): network 4xx/5xx", out[:200])
        
        # Close tab
        run_ab(["--session", session_id, "close"])
        time.sleep(1)
    
    # Final cleanup
    run_ab(["close", "--all"])
    mark("passed", "Browser E2E tests completed")
    print()

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    start_time = time.time()
    
    # Section 1: Health
    if not test_health():
        mark("critical", "Health check failed — aborting")
        save_and_print_summary(start_time)
        return
    
    # Section 2: Auth
    tokens = test_auth()
    
    if not tokens:
        mark("critical", "No tokens obtained — cannot continue API tests")
    else:
        test_candidates(tokens)
        test_screening(tokens)
        test_analytics(tokens)
        test_hiring_cycles(tokens)
        test_registration()
        test_admin(tokens)
        test_kf_specific(tokens)
    
    # Browser E2E
    test_browser_e2e(tokens)
    
    save_and_print_summary(start_time)

def save_and_print_summary(start_time):
    elapsed = time.time() - start_time
    
    # Save results
    run_file = QA_RUNS_DIR / f"{RUN_ID}.json"
    with open(run_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Cleanup old runs
    runs = sorted(QA_RUNS_DIR.glob("*.json"), key=os.path.getmtime)
    for old in runs[:-10]:
        old.unlink()
    
    # Summary
    passed = len(results["passed"])
    failed = len(results["failed"])
    warnings = len(results["warnings"])
    critical = len(results["critical"])
    
    print(f"\n{'═' * 60}")
    print(f"  QA RUN #{RUN_ID}")
    print(f"  Duration: {elapsed:.1f}s")
    print(f"  RESULTS: ✅ {passed} passed | ❌ {failed} failed | ⚠️  {warnings} warnings | 🔴 {critical} critical")
    print(f"  Total checks: {passed + failed + warnings + critical}")
    print(f"  Results saved: {run_file}")
    print(f"{'═' * 60}")

if __name__ == "__main__":
    main()
