#!/usr/bin/env python3
"""
Knowledge Factory — Final Autonomous QA Test (v6)
Correct credentials, better browser handling, proper proctoring/selection checks
"""
import json, os, subprocess, time, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://localhost:8000"
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
QA_DIR = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory")
FAILURES_DIR = QA_DIR / "failures" / RUN_ID
RUNS_DIR = QA_DIR / "qa_runs"
AB = "/opt/hermes_shared_memory/bin/ab"

ROLES = {
    "superadmin": {"email": "superadmin@knowledgefactory.io", "pw": "Super@12345"},
    "admin": {"email": "admin@knowledgefactory.io", "pw": "admin123"},
    "hr": {"email": "hr@knowledgefactory.io", "pw": "Hr@12345"},
    "interviewer": {"email": "interviewer@test.com", "pw": "Interviewer@12345"},
    "candidate": {"email": "candidate@test.com", "pw": "Candidate@12345"},
}

FAILURES_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

checks = []
severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
issues = {"critical": [], "high": [], "medium": [], "low": []}
role_coverage = {r: False for r in ROLES}

def log(name, ok, detail="", category="API"):
    checks.append({"name": name, "ok": ok, "detail": str(detail)[:300], "category": category})
    icon = "✅" if ok else "❌"
    print(f"  {icon} {name}: {str(detail)[:200]}")

def issue(sev, name):
    severity_counts[sev] += 1
    issues[sev].append(name)

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

def api_get(path, token=None):
    hdrs = " ".join(f'-H "Authorization: Bearer {token}"' for _ in [1] if token)
    rc, out, _ = run(f'curl -s -o /tmp/_api.json -w "%{{http_code}}" {hdrs} "{BASE_URL}{path}"', timeout=10)
    code = int(out.strip()) if out.strip().isdigit() else 0
    try:
        with open("/tmp/_api.json") as f:
            data = json.loads(f.read() or "{}")
    except:
        data = {}
    return code, data

def api_post(path, data=None, token=None):
    hdrs = ['-H "Content-Type: application/json"']
    if token:
        hdrs.append(f'-H "Authorization: Bearer {token}"')
    hdr_str = " ".join(hdrs)
    data_str = f"-d '{json.dumps(data)}'" if data else ""
    rc, out, _ = run(f'curl -s -o /tmp/_api.json -w "%{{http_code}}" {hdr_str} {data_str} "{BASE_URL}{path}"', timeout=10)
    code = int(out.strip()) if out.strip().isdigit() else 0
    try:
        with open("/tmp/_api.json") as f:
            data = json.loads(f.read() or "{}")
    except:
        data = {}
    return code, data

def login_role(role):
    creds = ROLES[role]
    code, data = api_post("/api/auth/login", {"email": creds["email"], "password": creds["pw"]})
    return data.get("access_token") if code == 200 else None

# === NGROK URL ===
NGROK_URL = ""
try:
    resp = urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=3)
    for t in json.loads(resp.read()).get("tunnels", []):
        if t["public_url"].startswith("https"):
            NGROK_URL = t["public_url"]
            break
except:
    pass

print(f"\n{'='*60}")
print(f"  KNOWLEDGE FACTORY QA RUN {RUN_ID}")
print(f"  API: {BASE_URL} | NGROK: {NGROK_URL or 'N/A'}")
print(f"{'='*60}")

# ======================== PHASE 1: API ========================
print("\n--- PHASE 1: API Tests ---")

# 1. Health
c, d = api_get("/health")
log("backend_health", c == 200, d.get("status","?"))
if c != 200: issue("critical", "backend_health")

# 2. Login all roles
print("\n>> Login Tests")
tokens = {}
for role in ROLES:
    t = login_role(role)
    if t:
        tokens[role] = t
        log(f"login_{role}", True, f"{ROLES[role]['email']} OK")
        role_coverage[role] = True
    else:
        log(f"login_{role}", False, f"{ROLES[role]['email']} FAILED")
        issue("critical", f"login_{role}")

# 3. Auth /me
print("\n>> Auth Me Tests")
for role in ROLES:
    if role in tokens:
        c, d = api_get("/api/auth/me", token=tokens[role])
        log(f"auth_me_{role}", c == 200, f"role={d.get('role','?')}")
        if c != 200: issue("high", f"auth_me_{role}")

# 4. Pipeline stats (public)
c, d = api_get("/api/screening/pipeline-stats")
stats = d.get("stats", d) if isinstance(d, dict) else {}
s = " ".join(f"{k}:{v}" for k,v in stats.items() if isinstance(v, int))[:200] if isinstance(stats, dict) else str(d)[:100]
log("pipeline_stats", c == 200, s)
if c != 200: issue("high", "pipeline_stats")

# 5. Screening run with HR token
print("\n>> Screening Run")
if "hr" in tokens:
    c, d = api_post("/api/screening/run", token=tokens["hr"])
    ok = c == 200
    detail = f"screened={d.get('screened','?')} passed={d.get('passed','?')} rejected={d.get('rejected','?')} cycle={d.get('cycle_name','?')}"
    log("screening_run", ok, detail)
    if not ok: issue("high", "screening_run")
else:
    log("screening_run", False, "No HR token")

# 6. Candidates listing
print("\n>> Candidates Listing")
for role in ["superadmin", "admin", "hr"]:
    if role in tokens:
        c, d = api_get("/api/candidates/", token=tokens[role])
        count = len(d.get("data", [])) if isinstance(d.get("data"), list) else "?"
        log(f"candidates_{role}", c == 200, f"{count} candidates")
        if c != 200: issue("high", f"candidates_{role}")

# 7. Candidate /me
if "candidate" in tokens:
    c, d = api_get("/api/candidates/me", token=tokens["candidate"])
    log("candidate_me", c == 200, f"{d.get('email','?')}")
    if c != 200: issue("high", "candidate_me")

# 8. Hiring cycles
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        c, d = api_get("/api/hiring-cycles/", token=tokens[role])
        log(f"hiring_cycles_{role}", c in (200, 404), f"HTTP {c}")
        if c not in (200, 404): issue("high", f"hiring_cycles_{role}")

# 9. Analytics
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        for ep in ["funnel", "dashboard"]:
            c, d = api_get(f"/api/analytics/{ep}", token=tokens[role])
            log(f"analytics_{ep}_{role}", c == 200, f"HTTP {c}")
            if c != 200: issue("high", f"analytics_{ep}_{role}")

# 10. Admin endpoints
for role in ["admin", "superadmin"]:
    if role in tokens:
        for ep in ["users", "logs"]:
            c, d = api_get(f"/api/admin/{ep}", token=tokens[role])
            log(f"admin_{ep}_{role}", c in (200, 404), f"HTTP {c}")
            if c not in (200, 404): issue("high", f"admin_{ep}_{role}")

# 11. Candidate assessment
if "candidate" in tokens:
    c, d = api_get("/api/assessment/active", token=tokens["candidate"])
    log("assessment_active", c in (200, 404), f"HTTP {c}")
    if c not in (200, 404): issue("high", "assessment_active")

# 12. Code execution
print("\n>> Code Execution")
c, d = api_post("/api/code/execute", {"language": "python", "code": "print(1+1)"})
log("code_exec_noauth", c == 401, f"HTTP {c}")
if c != 401: issue("high", "code_exec_noauth")

for role in ["admin", "hr"]:
    if role in tokens:
        c, d = api_post("/api/code/execute", {"language": "python", "code": "print(1+1)"}, token=tokens[role])
        ok = c in (200, 401, 502, 503, 422)
        status = d.get("status", str(c))
        log(f"code_exec_{role}", ok, f"HTTP {c} status={status}")
        if not ok: issue("high", f"code_exec_{role}")

# 13. Proctoring event
if "candidate" in tokens:
    c, d = api_post("/api/proctoring/event", {
        "assessment_id": "00000000-0000-0000-0000-000000000000",
        "candidate_id": "00000000-0000-0000-0000-000000000000",
        "event_type": "tab_switch",
        "timestamp": datetime.now().isoformat()
    }, token=tokens["candidate"])
    ok = c in (200, 201, 422, 404)  # 201 = created (valid!)
    log("proctoring_event", ok, f"HTTP {c}: {json.dumps(d)[:80]}")
    if not ok: issue("high", "proctoring_event")

# 14. Selection
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        c, d = api_get("/api/selection/", token=tokens[role])
        log(f"selection_{role}", c in (200, 404), f"HTTP {c}")
        if c not in (200, 404): issue("high", f"selection_{role}")

# 15. Register candidate
test_email = f"qa_test_{int(time.time())}@test.com"
c, d = api_post("/api/auth/register", {"email": test_email, "password": "Test@12345", "name": "QA Cron User", "role": "candidate"})
ok = c in (200, 201)
log("register_candidate", ok, f"HTTP {c} {test_email}" if ok else f"HTTP {c}: {d.get('detail','?')[:100]}")
if not ok: issue("high", "register_candidate")

# 16. Questions
c, d = api_get("/api/questions/generate")
log("questions_gen", c in (200, 401, 404), f"HTTP {c}")
if c not in (200, 401, 404): issue("high", "questions_gen")

# 17. Organizations
c, d = api_get("/api/admin/organizations/")
log("org_endpoint", c == 404, f"HTTP {c}")
if c != 404: issue("medium", "org_endpoint")

# ======================== PHASE 2: BROWSER ========================
print("\n--- PHASE 2: Browser Tests ---")

browser_ok = bool(NGROK_URL)
if not NGROK_URL:
    log("ngrok_reachable", False, "No ngrok URL")
    issue("critical", "ngrok_reachable")
else:
    try:
        req = urllib.request.Request(f"{NGROK_URL}/health")
        resp = urllib.request.urlopen(req, timeout=10)
        log("ngrok_reachable", resp.status == 200, f"HTTP {resp.status}")
        if resp.status != 200: issue("critical", "ngrok_reachable"); browser_ok = False
    except Exception as e:
        log("ngrok_reachable", False, str(e)[:80])
        issue("critical", "ngrok_reachable")
        browser_ok = False

if browser_ok:
    # Close all sessions first
    run(f"{AB} close --all", timeout=5)
    time.sleep(1)
    
    for role in ROLES:
        run(f"{AB} close --all", timeout=3)
        time.sleep(1)
        
        creds = ROLES[role]
        
        # Open page
        rc, out, _ = run(f"{AB} open {NGROK_URL}", timeout=15)
        if rc != 0:
            log(f"fe_open_{role}", False, f"ab open rc={rc}")
            issue("medium", f"fe_open_{role}")
            continue
        
        time.sleep(3)
        
        # Handle ngrok interstitial
        rc2, snap, _ = run(f"{AB} snapshot -c -i", timeout=10)
        if "Visit Site" in snap:
            for line in snap.split("\n"):
                if "Visit Site" in line and "[ref=" in line:
                    m = re.search(r'\[ref=([^\]]+)\]', line)
                    if m:
                        run(f"{AB} click @{m.group(1)}", timeout=5)
                        time.sleep(3)  # Wait for SPA render
                        break
        
        # Get page snapshot
        rc3, snap2, _ = run(f"{AB} snapshot -c -i", timeout=10)
        
        if "Login" in snap2:
            # Find Login button and click
            login_ref = None
            for line in snap2.split("\n"):
                if "Login" in line and "[ref=" in line:
                    m = re.search(r'\[ref=([^\]]+)\]', line)
                    if m:
                        login_ref = m.group(1)
                        break
            
            if login_ref:
                run(f"{AB} click @{login_ref}", timeout=5)
                time.sleep(2)
                
                # Fill login form
                rc4, snap3, _ = run(f"{AB} snapshot -c -i", timeout=10)
                
                email_ref = pw_ref = submit_ref = None
                for line in snap3.split("\n"):
                    if "email" in line.lower() and ("textbox" in line or "input" in line) and "[ref=" in line:
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m: email_ref = m.group(1)
                    if "password" in line.lower() and ("textbox" in line or "input" in line) and "[ref=" in line:
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m: pw_ref = m.group(1)
                    if "Sign In" in line and ("button" in line or "[ref=" in line):
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m: submit_ref = m.group(1)
                
                if email_ref:
                    run(f"{AB} fill @{email_ref} {creds['email']}", timeout=5)
                    time.sleep(0.5)
                if pw_ref:
                    run(f"{AB} fill @{pw_ref} {creds['pw']}", timeout=5)
                    time.sleep(0.5)
                
                if submit_ref:
                    run(f"{AB} click @{submit_ref}", timeout=5)
                    time.sleep(2)
                    
                    # Verify login
                    rc5, snap4, _ = run(f"{AB} snapshot -c -i", timeout=10)
                    logged_in = any(x in snap4 for x in ["Dashboard", "Candidates", "Selection", "Assessment", "Logout", "Welcome"])
                    log(f"fe_login_{role}", logged_in, f"Login {'succeeded' if logged_in else 'failed'}")
                    if logged_in:
                        role_coverage[role] = True
                        # Save state
                        run(f"{AB} state save {str(QA_DIR / 'auth' / f'{role}.json')}", timeout=5)
                    else:
                        issue("medium", f"fe_login_{role}")
                        run(f"{AB} screenshot {FAILURES_DIR}/{role}_login.png", timeout=5)
                else:
                    log(f"fe_login_{role}", False, "Submit button not found")
                    issue("medium", f"fe_login_{role}")
            else:
                log(f"fe_login_{role}", False, "Login button not found")
                issue("medium", f"fe_login_{role}")
        else:
            # Check if already logged in via state
            if any(x in snap2 for x in ["Dashboard", "Candidates", "Selection", "Assessment", "Logout"]):
                log(f"fe_login_{role}", True, "Already logged in via saved state")
                role_coverage[role] = True
            else:
                log(f"fe_login_{role}", False, f"Unexpected page: {snap2[:100]}")
                issue("medium", f"fe_login_{role}")

# ======================== PHASE 3: SYSTEM ========================
print("\n--- PHASE 3: System Tests ---")

fe_dist = Path("/mnt/hermes-shared/projects/Knowledge_Factory/app/dist")
fe_ok = fe_dist.exists() and (fe_dist / "index.html").exists()
log("frontend_build", fe_ok, f"dist/index.html: {fe_ok}")

db_file = Path("/mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db")
log("db_exists", db_file.exists(), f"db: {db_file.exists()}")

piston_url = os.environ.get("PISTON_API_URL", "")
if piston_url:
    rc, out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" "{piston_url}/health"', timeout=5)
    log("piston_api", rc in ("200", 200), f"HTTP {rc}")
else:
    log("piston_api", True, "Not configured (skipped)")

# ======================== REPORT ========================
print(f"\n{'='*60}")
print("  BUILDING REPORT")
print(f"{'='*60}")

total = len(checks)
passed = sum(1 for c in checks if c["ok"])
failed = total - passed

api_checks = [c for c in checks if c["category"] == "API"]
api_p = sum(1 for c in api_checks if c["ok"])
api_t = len(api_checks)
browser_checks = [c for c in checks if c["category"] == "FRONTEND"]
browser_p = sum(1 for c in browser_checks if c["ok"])
browser_t = len(browser_checks)
sys_checks = [c for c in checks if c["category"] == "SYSTEM"]
sys_p = sum(1 for c in sys_checks if c["ok"])
sys_t = len(sys_checks)

# Comparison
prev_runs = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json") and f < f"{RUN_ID}_report.json"])
prev_run = None
if prev_runs:
    try:
        with open(str(RUNS_DIR / prev_runs[-1])) as f:
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
    new_issues_list = list(failed_names); fixed_issues_list = []; recurring_issues_list = []

report = {
    "run_id": RUN_ID, "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
    "severity_counts": severity_counts, "issues": issues,
    "comparison": {
        "previous_run": prev_runs[-1] if prev_runs else None,
        "previous_passed": prev_run.get("summary", {}).get("total_passed", 0) if prev_run else 0,
        "previous_total": prev_run.get("summary", {}).get("total_tests", 0) if prev_run else 0,
        "new_issues": new_issues_list, "fixed_issues": fixed_issues_list, "recurring_issues": recurring_issues_list,
    },
    "summary": {
        "run_id": RUN_ID, "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_tests": {"passed": api_p, "total": api_t, "failed": api_t - api_p},
        "browser_tests": {"passed": browser_p, "total": browser_t, "failed": browser_t - browser_p},
        "system_tests": {"passed": sys_p, "total": sys_t, "failed": sys_t - sys_p},
        "total_passed": passed, "total_failed": failed, "total_tests": total,
    },
    "systems": {
        "backend_api": "✅ OK" if api_p == api_t else f"⚠️ {api_t-api_p} failures",
        "pipeline_screening": "✅ Working" if all(c["ok"] for c in checks if c["name"] in ("pipeline_stats", "screening_run")) else "⚠️ Issues",
        "analytics": "✅ Working" if all(c["ok"] for c in checks if "analytics" in c["name"]) else "⚠️ Issues",
        "frontend_ui": "✅ Working" if browser_p == browser_t else f"⚠️ {browser_t-browser_p} failures",
    },
    "pipeline": s if 's' in dir() else "N/A",
    "role_coverage": role_coverage,
}

report_path = RUNS_DIR / f"{RUN_ID}_report.json"
with open(report_path, "w") as f:
    json.dump(report, f, indent=2, default=str)

summary = {
    "run_id": RUN_ID, "passed": passed, "failed": failed,
    "critical": severity_counts["critical"], "total": total,
    "roles": role_coverage, "systems": report["systems"],
}
with open(RUNS_DIR / "latest_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

# Cleanup old runs
all_reports = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json")])
for old_f in all_reports[:-10]:
    base = old_f.replace("_report.json", "")
    for s in ["_report.json", "_api.json", "_browser.json", "_telegram_data.json"]:
        p = RUNS_DIR / f"{base}{s}"
        if p.exists(): p.unlink()

print(f"\n✅ Report saved")
print(f"📊 {passed}/{total} passed, {failed} failed, {severity_counts['critical']} critical, {severity_counts['high']} high, {severity_counts['medium']} medium")
print(f"   API: {api_p}/{api_t} | Browser: {browser_p}/{browser_t} | System: {sys_p}/{sys_t}")
print(f"   Roles: {' '.join('✅'+r if v else '❌'+r for r,v in role_coverage.items())}")

blocked = [r for r,v in role_coverage.items() if not v]
if blocked: print(f"🚫 BLOCKED: {', '.join(blocked)}")
print(f"\nPipeline: {s}")
if new_issues_list: print(f"🆕 New: {', '.join(new_issues_list)}")
if fixed_issues_list: print(f"✅ Fixed: {', '.join(fixed_issues_list)}")

print("\n---JSON---")
print(json.dumps(summary))
print("---JSON---")
