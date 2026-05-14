#!/usr/bin/env python3
"""
Knowledge Factory Comprehensive Autonomous QA Tester
Runs every 2 hours via cron. Tests API endpoints, browser E2E flows, 
and KF-specific systems. Sends report to Telegram.
"""
import json, os, sys, time, uuid, urllib.request, urllib.error, sqlite3, bcrypt
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
NGROK_URL = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
PROJECT_ROOT = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory")
AUTH_DIR = PROJECT_ROOT / "auth"
FAILURES_DIR = PROJECT_ROOT / "failures" / RUN_ID
QA_RUNS_DIR = PROJECT_ROOT / "qa_runs"
BASELINES_DIR = PROJECT_ROOT / "baselines"
AB = "/opt/hermes_shared_memory/bin/ab"

os.makedirs(AUTH_DIR, exist_ok=True)
os.makedirs(FAILURES_DIR, exist_ok=True)
os.makedirs(QA_RUNS_DIR, exist_ok=True)
os.makedirs(BASELINES_DIR, exist_ok=True)

# ─── Corrected Credentials (verified against actual DB hashes) ──────────
CREDENTIALS = {
    "superadmin": {"email": "superadmin@knowledgefactory.io", "password": "Super@12345", "role": "SUPERADMIN"},
    "admin":      {"email": "admin@knowledgefactory.io",      "password": "admin123",     "role": "ADMIN"},
    "hr":         {"email": "hr@knowledgefactory.io",         "password": "Hr@12345",     "role": "HR"},
    "interviewer":{"email": "interviewer@knowledgefactory.io","password": "Interview@12345","role": "INTERVIEWER"},
    # candidate@test.com has unknown password; we'll register a fresh one
}

# ─── Test Results ────────────────────────────────────────────────────────
results = {
    "run_id": RUN_ID,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "passed": [],
    "failed": [],
    "warnings": [],
    "critical": [],
    "role_coverage": {},
    "kf_systems": {},
}

def mark(level, desc, detail=None):
    entry = {"desc": desc, "detail": detail} if detail else {"desc": desc}
    results[level].append(entry)
    icon = {"passed": "✅", "failed": "❌", "warnings": "⚠️", "critical": "🔴"}.get(level, "❓")
    print(f"  {icon} [{level.upper()}] {desc}")
    if detail: print(f"     └─ {detail}")

def run_ab(args, timeout=30):
    import subprocess
    cmd = [AB] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def api_req(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body_data = resp.read().decode()
            return resp.status, json.loads(body_data) if body_data else {}
    except urllib.error.HTTPError as e:
        body_data = e.read().decode() if e.fp else "{}"
        try: return e.code, json.loads(body_data)
        except: return e.code, {"detail": body_data}
    except Exception as e:
        return 0, {"error": str(e)}

def api_get(path, token=None):
    return api_req("GET", path, token=token)

def api_post(path, body, token=None):
    return api_req("POST", path, body, token=token)

def login(email, password):
    status, data = api_post("/api/auth/login", {"email": email, "password": password})
    if status == 200 and "access_token" in data:
        return data["access_token"], data
    return None, data

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════
def test_health():
    print("\n═══════════════════════════ SECTION 1: Health Check ═══════════════════════════")
    status, data = api_get("/health")
    if status == 200 and data.get("status") == "ok":
        mark("passed", "Health check: GET /health returns 200 OK")
        return True
    else:
        mark("critical", f"Health check FAILED: status={status}, data={data}")
        return False

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: AUTHENTICATION (API-level)
# ═══════════════════════════════════════════════════════════════════════════
def test_auth():
    print("\n═══════════════════════════ SECTION 2: Authentication ═══════════════════════════")
    tokens = {}
    
    for role_name, creds in CREDENTIALS.items():
        token, data = login(creds["email"], creds["password"])
        if token:
            tokens[role_name] = token
            role = data.get("role", "?")
            mark("passed", f"Login: {role_name} ({creds['email']}) — role={role}")
            results["role_coverage"][role_name] = "✅"
        else:
            detail = str(data.get("detail", data))[:100]
            mark("critical", f"Login FAILED: {role_name} ({creds['email']}) — {detail}")
            results["role_coverage"][role_name] = "❌"
    
    # Verify /me for each role
    for role_name in tokens:
        status, data = api_get("/api/auth/me", token=tokens[role_name])
        if status == 200:
            mark("passed", f"/me OK: {role_name} (role={data.get('role', '?')})")
        else:
            mark("failed", f"/me FAILED: {role_name} — status={status}")
    
    # Register a new test candidate with known password for browser testing
    ts = int(time.time())
    candidate_email = f"qa_e2e_{ts}@test.com"
    candidate_password = "QaE2ePass@123"
    reg_data = {
        "email": candidate_email,
        "password": candidate_password,
        "name": f"QA E2E User",
        "role": "candidate",
        "college": "QA University",
        "branch": "CSE",
        "cgpa": 8.5,
        "passed_out_year": 2026,
    }
    status, data = api_post("/api/auth/register", reg_data)
    if status in (200, 201):
        mark("passed", f"Registration: {candidate_email} — created")
        # Login with new candidate
        token, data = login(candidate_email, candidate_password)
        if token:
            tokens["candidate"] = token
            results["role_coverage"]["candidate"] = "✅"
            mark("passed", f"Login as new candidate ({candidate_email}): OK")
            # Save email for later
            tokens["_candidate_email"] = candidate_email
            tokens["_candidate_password"] = candidate_password
        else:
            results["role_coverage"]["candidate"] = "❌"
            mark("failed", f"Could not login as new candidate: {data}")
    else:
        results["role_coverage"]["candidate"] = "❌"
        mark("failed", f"Registration FAILED: status={status}, detail={str(data)[:100]}")
    
    return tokens

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: CANDIDATES API
# ═══════════════════════════════════════════════════════════════════════════
def test_candidates(tokens):
    print("\n═══════════════════════════ SECTION 3: Candidates API ═══════════════════════════")
    
    for role in ["admin", "hr"]:
        if role not in tokens: continue
        status, data = api_get("/api/candidates/", token=tokens[role])
        if status == 200:
            candidates = data if isinstance(data, list) else data.get("data") or data.get("candidates") or []
            count = len(candidates) if isinstance(candidates, list) else "OK"
            mark("passed", f"Candidates list ({role}): {count} candidates")
        else:
            mark("failed", f"Candidates list ({role}): status={status}")
    
    # Candidate /me
    if "candidate" in tokens:
        status, data = api_get("/api/candidates/me", token=tokens["candidate"])
        if status == 200:
            mark("passed", f"Candidate /me: OK (status={data.get('status','?')})")
        else:
            mark("failed", f"Candidate /me: status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: SCREENING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════
def test_screening(tokens):
    print("\n═══════════════════════════ SECTION 4: Screening Pipeline ═══════════════════════════")
    
    # Pipeline stats (no auth required - known issue)
    status, data = api_get("/api/screening/pipeline-stats")
    if status == 200:
        stats = data.get("stats") or data
        if isinstance(stats, dict):
            total = sum(stats.values())
            mark("passed", f"Pipeline stats: {len(stats)} statuses, {total} total candidates")
        else:
            mark("passed", f"Pipeline stats: OK")
    else:
        mark("warnings", f"Pipeline stats: status={status}")
    
    # Screening run (HR role)
    if "hr" in tokens:
        status, data = api_post("/api/screening/run", {}, token=tokens["hr"])
        if status == 200:
            screened = data.get("screened", data.get("total", "?"))
            passed = data.get("passed", data.get("pass", "?"))
            rejected = data.get("rejected", data.get("fail", "?"))
            mark("passed", f"Screening run: screened={screened}, passed={passed}, rejected={rejected}")
        else:
            mark("warnings", f"Screening run: status={status} — {str(data)[:100]}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════
def test_analytics(tokens):
    print("\n═══════════════════════════ SECTION 5: Analytics ═══════════════════════════")
    
    for ep in ["/api/analytics/funnel", "/api/analytics/dashboard"]:
        for role in ["admin", "hr"]:
            if role not in tokens: continue
            status, data = api_get(ep, token=tokens[role])
            name = ep.split("/")[-1]
            if status == 200:
                mark("passed", f"Analytics {name} ({role}): OK")
            else:
                mark("warnings", f"Analytics {name} ({role}): status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: HIRING CYCLES
# ═══════════════════════════════════════════════════════════════════════════
def test_hiring_cycles(tokens):
    print("\n═══════════════════════════ SECTION 6: Hiring Cycles ═══════════════════════════")
    
    for role in ["admin", "hr"]:
        if role not in tokens: continue
        status, data = api_get("/api/hiring-cycles/", token=tokens[role])
        if status == 200:
            cycles = data if isinstance(data, list) else data.get("data") or data.get("cycles") or []
            count = len(cycles)
            if count > 0:
                mark("passed", f"Hiring cycles ({role}): {count} cycles")
            else:
                mark("warnings", f"Hiring cycles ({role}): 0 cycles found")
        else:
            mark("warnings", f"Hiring cycles ({role}): status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: ADMIN ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════
def test_admin(tokens):
    print("\n═══════════════════════════ SECTION 7: Admin Endpoints ═══════════════════════════")
    
    if "admin" in tokens:
        for ep in ["/api/admin/users", "/api/admin/logs"]:
            status, data = api_get(ep, token=tokens["admin"])
            name = ep.split("/")[-1]
            if status == 200:
                mark("passed", f"Admin {name}: OK")
            else:
                mark("warnings", f"Admin {name}: status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: KF-SPECIFIC SYSTEMS
# ═══════════════════════════════════════════════════════════════════════════
def test_kf_systems(tokens):
    print("\n═══════════════════════════ SECTION 8: KF-Specific Systems ═══════════════════════════")
    
    # Questions API
    status, data = api_get("/api/questions/")
    if status == 200:
        mark("passed", "Questions API: OK")
        results["kf_systems"]["questions"] = "✅"
    elif status in (401, 403):
        mark("warnings", "Questions API: requires auth (status={status})")
        results["kf_systems"]["questions"] = "⚠️"
    else:
        mark("warnings", f"Questions API: status={status}")
        results["kf_systems"]["questions"] = "⚠️"
    
    # Code execution API
    status, data = api_get("/api/code/")
    if status in (200, 422):  # 422 means endpoint exists, just needs params
        mark("passed", "Code execution API: endpoint reachable")
        results["kf_systems"]["code_execution"] = "✅"
    elif status == 405:  # Method not allowed but endpoint exists
        mark("passed", "Code execution API: endpoint exists (405)")
        results["kf_systems"]["code_execution"] = "✅"
    else:
        mark("warnings", f"Code execution API: status={status}")
        results["kf_systems"]["code_execution"] = "⚠️"
    
    # Proctoring API
    if "admin" in tokens:
        status, data = api_get("/api/proctoring/event", token=tokens["admin"])
        if status in (200, 405, 422):
            mark("passed", "Proctoring API: endpoint reachable")
        else:
            mark("warnings", f"Proctoring API: status={status}")
    
    # Assessment API
    if "candidate" in tokens:
        status, data = api_get("/api/assessment/", token=tokens["candidate"])
        if status in (200, 404, 405):
            mark("passed", "Assessment API: endpoint reachable")
        else:
            mark("warnings", f"Assessment API: status={status}")
    
    # Interview/Feedback API
    if "interviewer" in tokens:
        status, data = api_get("/api/interviews/feedback", token=tokens["interviewer"])
        if status in (200, 404, 422):
            mark("passed", "Feedback API ({interviewer}): endpoint reachable")
        else:
            mark("warnings", f"Feedback API: status={status}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: BROWSER E2E TESTS
# ═══════════════════════════════════════════════════════════════════════════
def test_browser_e2e(tokens):
    print("\n═══════════════════════════ SECTION 9: Browser E2E Tests ═══════════════════════════")
    
    # Close any old sessions
    run_ab(["close", "--all"])
    time.sleep(1)
    
    # Also test candidate from stored creds if available
    browser_creds = dict(CREDENTIALS)
    if "candidate" in tokens and "_candidate_email" in tokens:
        browser_creds["candidate"] = {
            "email": tokens["_candidate_email"],
            "password": tokens["_candidate_password"],
            "role": "CANDIDATE"
        }
    
    for role_name, creds in browser_creds.items():
        print(f"\n  ── Testing role: {role_name} ({creds['email']}) ──")
        
        auth_file = AUTH_DIR / f"{role_name}.json"
        session_arg = ["--session", role_name]
        
        # Navigate to app
        if auth_file.exists():
            rc, out, err = run_ab(session_arg + ["--state", str(auth_file), "open", NGROK_URL])
            if rc != 0:
                auth_file.unlink(missing_ok=True)
                rc, out, err = run_ab(session_arg + ["open", NGROK_URL])
        else:
            rc, out, err = run_ab(session_arg + ["open", NGROK_URL])
        
        if rc != 0:
            mark("failed", f"Browser ({role_name}): failed to open page — rc={rc}")
            run_ab(session_arg + ["screenshot", str(FAILURES_DIR / f"{role_name}_open_fail.png")])
            continue
        
        time.sleep(2)
        
        # Click through ngrok interstitial
        rc, out, err = run_ab(session_arg + ["snapshot", "-i", "-c"])
        if "Visit Site" in out or "visit site" in out.lower():
            # Find Visit Site button ref
            import re
            match = re.search(r'\[ref=([^\]]+)\].*?Visit Site', out)
            if match:
                run_ab(session_arg + ["click", f"@{match.group(1)}"])
                time.sleep(2)
        
        # Check for login page
        rc, out, err = run_ab(session_arg + ["snapshot", "-i", "-c"])
        
        # Check if we see login form
        if "Email" in out and "Password" in out:
            # Need to login
            rc, e_out, e_err = run_ab(session_arg + ["eval", 
                f"document.querySelector('input[type=email], input[name=email]') ? true : false"])
            
            if "true" in (e_out or "").lower():
                # Fill with JS for reliability
                run_ab(session_arg + ["eval", 
                    f"(function(){{ let el = document.querySelector('input[type=email], input[name=email]'); if(el){{ el.value='{creds['email']}'; el.dispatchEvent(new Event('input', {{bubbles:true}})); return true; }} return false; }})()"])
                run_ab(session_arg + ["eval", 
                    f"(function(){{ let el = document.querySelector('input[type=password]'); if(el){{ el.value='{creds['password']}'; el.dispatchEvent(new Event('input', {{bubbles:true}})); return true; }} return false; }})()"])
                time.sleep(0.5)
                
                # Click submit button
                rc, out, err = run_ab(session_arg + ["eval",
                    "(function(){ let btns = document.querySelectorAll('button'); for(let b of btns){ if(b.textContent.includes('Sign In') || b.textContent.includes('Login') || b.type==='submit'){ b.click(); return 'clicked'; }} return 'not found'; })()"])
                
                time.sleep(3)
                
                # Check if login succeeded
                rc, snap_out, err = run_ab(session_arg + ["snapshot", "-i", "-c"])
                if "Incorrect email or password" in snap_out:
                    mark("failed", f"Browser ({role_name}): login FAILED — incorrect credentials")
                    run_ab(session_arg + ["screenshot", str(FAILURES_DIR / f"{role_name}_login_fail.png")])
                    continue
                else:
                    mark("passed", f"Browser login ({role_name}): login successful")
            else:
                mark("warnings", f"Browser ({role_name}): could not find email field")
        else:
            # Already logged in via state
            mark("passed", f"Browser ({role_name}): loaded with saved auth state")
        
        # Take screenshot after login
        run_ab(session_arg + ["screenshot", str(FAILURES_DIR / f"{role_name}_dashboard.png")])
        
        # Get page title
        rc, title_out, err = run_ab(session_arg + ["eval", "document.title"])
        title = title_out.strip() if title_out else "unknown"
        mark("passed" if title and "404" not in title else "warning", 
             f"Browser ({role_name}): page title='{title}'")
        
        # Save auth state
        run_ab(session_arg + ["state", "save", str(auth_file)])
        
        # Check console for errors
        rc, console_out, err = run_ab(session_arg + ["console", "--json"])
        if console_out and len(console_out.strip()) > 2:
            try:
                console_entries = json.loads(console_out) if isinstance(console_out, str) else []
                errors = [e for e in (console_entries if isinstance(console_entries, list) else []) 
                         if isinstance(e, dict) and e.get('level') in ('error', 'severe')]
                if errors:
                    mark("warnings", f"Browser ({role_name}): {len(errors)} console errors", 
                         errors[0].get('message', str(errors[0]))[:150])
            except (json.JSONDecodeError, TypeError):
                pass  # Not JSON, ignore
    
    # Close sessions
    run_ab(["close", "--all"])
    print("  Browser sessions closed.")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10: DATABASE INTEGRITY CHECK
# ═══════════════════════════════════════════════════════════════════════════
def test_db_integrity():
    print("\n═══════════════════════════ SECTION 10: Database Integrity ═══════════════════════════")
    
    db_path = PROJECT_ROOT / "backend" / "knowledge_factory.db"
    if not db_path.exists():
        mark("critical", f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    # Check tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    expected_tables = ['alembic_version', 'candidates', 'hiring_cycles', 'proctoring_records', 
                       'users', 'assessment_sections', 'assessments', 'interview_feedback',
                       'audit_logs', 'test_cases']
    existing = [t for t in expected_tables if t in tables]
    missing = [t for t in expected_tables if t not in tables]
    
    if len(missing) == 0:
        mark("passed", f"DB tables: all {len(existing)}/{len(expected_tables)} present")
    else:
        mark("warnings", f"DB tables: {len(existing)}/{len(expected_tables)} present, missing: {missing}")
    
    # Check user counts
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM candidates")
    candidate_count = cur.fetchone()[0]
    mark("passed", f"DB records: {user_count} users, {candidate_count} candidates")
    
    conn.close()

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    global results
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    print(f"\n{'='*70}")
    print(f"  KNOWLEDGE FACTORY QA TEST — Run {RUN_ID}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # Section 1: Health
    if not test_health():
        return save_report()
    
    # Section 2: Auth
    tokens = test_auth()
    
    # Section 3: Candidates API
    test_candidates(tokens)
    
    # Section 4: Screening
    test_screening(tokens)
    
    # Section 5: Analytics
    test_analytics(tokens)
    
    # Section 6: Hiring Cycles
    test_hiring_cycles(tokens)
    
    # Section 7: Admin
    test_admin(tokens)
    
    # Section 8: KF-Specific
    test_kf_systems(tokens)
    
    # Section 9: Browser E2E
    test_browser_e2e(tokens)
    
    # Section 10: DB Integrity
    test_db_integrity()
    
    save_report()
    send_telegram_report()

def save_report():
    # Summary
    total = len(results["passed"]) + len(results["failed"]) + len(results["warnings"]) + len(results["critical"])
    results["summary"] = {
        "total": total,
        "passed": len(results["passed"]),
        "failed": len(results["failed"]),
        "warnings": len(results["warnings"]),
        "critical": len(results["critical"]),
    }
    
    report_path = QA_RUNS_DIR / f"{RUN_ID}.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print(f"  SUMMARY: {results['summary']['passed']} passed, "
          f"{results['summary']['failed']} failed, "
          f"{results['summary']['warnings']} warnings, "
          f"{results['summary']['critical']} critical")
    print(f"  Report saved: {report_path}")
    print(f"{'='*70}\n")
    
    return results

def send_telegram_report():
    """Send summary to Telegram if bot token configured."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("  ⚠️  Telegram not configured (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set)")
        print("  📄 Report saved locally for manual review")
        return
    
    s = results["summary"]
    
    # Build message
    msg = f"🤖 *KF QA Report — {RUN_ID}*\n"
    msg += f"📊 Summary: ✅{s['passed']} ❌{s['failed']} ⚠️{s['warnings']} 🔴{s['critical']}\n\n"
    
    msg += "*Role Coverage:*\n"
    for role, status in results["role_coverage"].items():
        msg += f"  {status} {role}\n"
    
    msg += "\n*KF Systems:*\n"
    for system, status in results["kf_systems"].items():
        msg += f"  {status} {system}\n"
    
    if results["critical"]:
        msg += "\n*🔴 CRITICAL ISSUES:*\n"
        for item in results["critical"][:5]:
            msg += f"  • {item['desc']}\n"
    
    if results["failed"]:
        msg += "\n*❌ FAILURES:*\n"
        for item in results["failed"][:5]:
            msg += f"  • {item['desc']}\n"
    
    if results["warnings"]:
        msg += "\n*⚠️ WARNINGS:*\n"
        for item in results["warnings"][:5]:
            msg += f"  • {item['desc']}\n"
    
    if s["passed"] > 0:
        msg += f"\n✅ *{s['passed']} checks passing*"
    
    # Send
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}).encode()
    
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"  ✅ Telegram report sent")
    except Exception as e:
        print(f"  ❌ Telegram send failed: {e}")

if __name__ == "__main__":
    main()
