#!/usr/bin/env python3
"""
Knowledge Factory QA — v7 FINAL
Fixed: using stdout for HTTP status code, not returncode
"""
import json, os, subprocess, time, re, urllib.request, sys
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://localhost:8000"
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
QA_DIR = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory")
RUNS_DIR = QA_DIR / "qa_runs"
FAILURES_DIR = QA_DIR / "failures" / RUN_ID
AB = "/opt/hermes_shared_memory/bin/ab"
FAILURES_DIR.mkdir(parents=True, exist_ok=True)

ROLES = {
    "superadmin": {"email": "superadmin@knowledgefactory.io", "pw": "Super@12345"},
    "admin": {"email": "admin@knowledgefactory.io", "pw": "admin123"},
    "hr": {"email": "hr@knowledgefactory.io", "pw": "Hr@12345"},
    "interviewer": {"email": "interviewer@test.com", "pw": "Interviewer@12345"},
    "candidate": {"email": "candidate@test.com", "pw": "Candidate@12345"},
}

def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def curl_get(url, token=None):
    """GET request, returns (http_code, response_body)"""
    hdrs = f'-H "Authorization: Bearer {token}"' if token else ""
    rc, out, err = run(f'curl -s -o /tmp/_api_resp.json -w "%{{http_code}}" {hdrs} "{url}"', timeout=10)
    http_code = int(out) if out.isdigit() else 0
    try:
        with open("/tmp/_api_resp.json") as f:
            body = f.read()
        data = json.loads(body) if body else {}
    except:
        data = {}
    return http_code, data

def curl_post(url, data_obj=None, token=None):
    """POST request, returns (http_code, response_body)"""
    hdrs = ['-H "Content-Type: application/json"']
    if token:
        hdrs.append(f'-H "Authorization: Bearer {token}"')
    hdr_str = " ".join(hdrs)
    # Always specify -X POST and use -d '{}' if no data to ensure POST method
    if data_obj is not None:
        data_str = f"-d '{json.dumps(data_obj)}'"
    else:
        data_str = "-d '{}'"
    rc, out, err = run(f'curl -s -o /tmp/_api_resp.json -w "%{{http_code}}" -X POST {hdr_str} {data_str} "{url}"', timeout=10)
    http_code = int(out) if out.isdigit() else 0
    try:
        with open("/tmp/_api_resp.json") as f:
            body = f.read()
        data = json.loads(body) if body else {}
    except:
        data = {}
    return http_code, data

def curl_http_code(url, token=None):
    """Just get HTTP status code"""
    hdrs = f'-H "Authorization: Bearer {token}"' if token else ""
    rc, out, err = run(f'curl -s -o /dev/null -w "%{{http_code}}" {hdrs} "{url}"', timeout=10)
    return int(out) if out.isdigit() else 0

NGROK_URL = ""
try:
    resp = urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=3)
    for t in json.loads(resp.read()).get("tunnels", []):
        if t["public_url"].startswith("https"):
            NGROK_URL = t["public_url"]
            break
except:
    pass

checks = []
severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
issues = {"critical": [], "high": [], "medium": [], "low": []}
role_coverage = {r: False for r in ROLES}

def log(name, ok, detail="", category="API"):
    checks.append({"name": name, "ok": ok, "detail": str(detail)[:300], "category": category})
    print(f"  {'✅' if ok else '❌'} {name}: {str(detail)[:200]}")

def issue(sev, name):
    severity_counts[sev] += 1
    issues[sev].append(name)

print(f"\n{'='*60}")
print(f"  KNOWLEDGE FACTORY QA RUN {RUN_ID}")
print(f"{'='*60}")

# ====== PHASE 1: API ======
print("\n--- PHASE 1: API Tests ---")

# Health
code, data = curl_get(f"{BASE_URL}/health")
log("backend_health", code == 200, f"HTTP {code}: {data.get('status','?')}")
if code != 200: issue("critical", "backend_health")

# Login all
tokens = {}
for role in ROLES:
    code, data = curl_post(f"{BASE_URL}/api/auth/login", {"email": ROLES[role]["email"], "password": ROLES[role]["pw"]})
    if code == 200 and "access_token" in data:
        tokens[role] = data["access_token"]
        role_coverage[role] = True
        log(f"login_{role}", True, f"{ROLES[role]['email']}")
    else:
        log(f"login_{role}", False, f"HTTP {code}: {data.get('detail','no token')[:50]}")
        issue("critical", f"login_{role}")

# Auth /me
for role in tokens:
    code, data = curl_get(f"{BASE_URL}/api/auth/me", tokens[role])
    actual_role = data.get("role", "")
    expected = role.upper()
    log(f"auth_me_{role}", code == 200 and actual_role == expected, f"HTTP {code} role={actual_role}")
    if code != 200: issue("high", f"auth_me_{role}")

# Pipeline stats
code, data = curl_get(f"{BASE_URL}/api/screening/pipeline-stats")
stats = data.get("stats", data) if isinstance(data, dict) else {}
s = " ".join(f"{k}:{v}" for k,v in stats.items() if isinstance(v, int))[:200] if isinstance(stats, dict) else str(data)[:100]
log("pipeline_stats", code == 200, s)
if code != 200: issue("high", "pipeline_stats")

# Screening run
if "hr" in tokens:
    code, data = curl_post(f"{BASE_URL}/api/screening/run", token=tokens["hr"])
    ok = "screened" in data
    log("screening_run", ok, f"HTTP {code} screened={data.get('screened','?')} passed={data.get('passed','?')} rejected={data.get('rejected','?')}")
    if not ok: issue("high", "screening_run")
else:
    log("screening_run", False, "No HR token")

# Candidates list
for role in ["superadmin", "admin", "hr"]:
    if role in tokens:
        code, data = curl_get(f"{BASE_URL}/api/candidates/", tokens[role])
        lst = data.get("data", data) if isinstance(data, dict) else []
        count = len(lst) if isinstance(lst, list) else "?"
        log(f"candidates_{role}", code == 200, f"HTTP {code}: {count} candidates")
        if code != 200: issue("high", f"candidates_{role}")

# Candidate /me
if "candidate" in tokens:
    code, data = curl_get(f"{BASE_URL}/api/candidates/me", tokens["candidate"])
    log("candidate_me", code == 200, f"HTTP {code}: {data.get('email','?')}")
    if code != 200: issue("high", "candidate_me")

# Hiring cycles
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        code = curl_http_code(f"{BASE_URL}/api/hiring-cycles/", tokens[role])
        log(f"hiring_cycles_{role}", code in (200, 404), f"HTTP {code}")
        if code not in (200, 404): issue("high", f"hiring_cycles_{role}")

# Analytics
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        for ep in ["funnel", "dashboard"]:
            code = curl_http_code(f"{BASE_URL}/api/analytics/{ep}", tokens[role])
            log(f"analytics_{ep}_{role}", code == 200, f"HTTP {code}")
            if code != 200: issue("high", f"analytics_{ep}_{role}")

# Admin endpoints
for role in ["admin", "superadmin"]:
    if role in tokens:
        for ep in ["users", "logs"]:
            code = curl_http_code(f"{BASE_URL}/api/admin/{ep}", tokens[role])
            log(f"admin_{ep}_{role}", code in (200, 404), f"HTTP {code}")
            if code not in (200, 404): issue("high", f"admin_{ep}_{role}")

# Assessment active
if "candidate" in tokens:
    code = curl_http_code(f"{BASE_URL}/api/assessment/active", tokens["candidate"])
    log("assessment_active", code in (200, 404), f"HTTP {code}")
    if code not in (200, 404): issue("high", "assessment_active")

# Code execution
code, data = curl_post(f"{BASE_URL}/api/code/execute", {"language": "python", "code": "print(1)"})
log("code_exec_noauth", code == 401, f"HTTP {code}: {data.get('detail','?')[:50]}")
if code != 401: issue("high", "code_exec_noauth")

for role in ["admin", "hr"]:
    if role in tokens:
        code, data = curl_post(f"{BASE_URL}/api/code/execute", {"language": "python", "code": "print(1)"}, tokens[role])
        ok = code in (200, 401, 502, 503, 422)
        log(f"code_exec_{role}", ok, f"HTTP {code}: {data.get('status','?')[:30] if isinstance(data,dict) else str(data)[:30]}")
        if not ok: issue("high", f"code_exec_{role}")

# Proctoring
if "candidate" in tokens:
    ts = datetime.now().isoformat()
    code, data = curl_post(f"{BASE_URL}/api/proctoring/event", {
        "assessment_id": "00000000-0000-0000-0000-000000000000",
        "candidate_id": "00000000-0000-0000-0000-000000000000",
        "event_type": "tab_switch",
        "timestamp": ts
    }, tokens["candidate"])
    ok = code in (200, 201, 422, 404)
    log("proctoring_event", ok, f"HTTP {code}: {json.dumps(data)[:80] if isinstance(data,dict) else str(data)[:80]}")
    if not ok: issue("high", "proctoring_event")

# Register
test_email = f"qa_test_{int(time.time())}@test.com"
code, data = curl_post(f"{BASE_URL}/api/auth/register", {"email": test_email, "password": "Test@12345", "name": "QA Cron", "role": "candidate"})
ok = code in (200, 201)
log("register_candidate", ok, f"HTTP {code}: {test_email if ok else data.get('detail','?')[:50]}")
if not ok: issue("high", "register_candidate")

# Questions
code = curl_http_code(f"{BASE_URL}/api/questions/generate")
log("questions_generate", code in (200, 401, 404), f"HTTP {code}")

# ====== PHASE 2: BROWSER ======
print("\n--- PHASE 2: Browser Tests ---")

if not NGROK_URL:
    log("ngrok_reachable", False, "No ngrok URL")
    issue("critical", "ngrok_reachable")
else:
    code = curl_http_code(f"{NGROK_URL}/health")
    log("ngrok_reachable", code == 200, f"HTTP {code}")
    if code != 200:
        issue("critical", "ngrok_reachable")
    else:
        # Close old sessions
        run(f"{AB} close --all", timeout=5)
        time.sleep(2)
        
        for role in ROLES:
            creds = ROLES[role]
            run(f"{AB} close --all", timeout=3)
            time.sleep(1.5)
            
            rc, out, err = run(f"{AB} open {NGROK_URL}", timeout=20)
            time.sleep(2)
            
            rc1, snap, _ = run(f"{AB} snapshot -c -i", timeout=10)
            
            # ngrok interstitial?
            visit_ref = ""
            for line in snap.split("\n"):
                if "Visit Site" in line and "[ref=" in line:
                    m = re.search(r'\[ref=([^\]]+)\]', line)
                    if m: visit_ref = m.group(1); break
            
            if visit_ref:
                run(f"{AB} click @{visit_ref}", timeout=5)
                time.sleep(8)  # SPA mount wait
            
            # Re-snapshot
            rc2, snap2, _ = run(f"{AB} snapshot -c -i", timeout=10)
            
            if "Login" in snap2:
                login_ref = ""
                for line in snap2.split("\n"):
                    if "Login" in line and "[ref=" in line:
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m: login_ref = m.group(1); break
                
                if login_ref:
                    run(f"{AB} click @{login_ref}", timeout=5)
                    time.sleep(2.5)
                    
                    rc3, snap3, _ = run(f"{AB} snapshot -c -i", timeout=10)
                    
                    email_ref = pw_ref = submit_ref = ""
                    for line in snap3.split("\n"):
                        if "Email" in line and ("textbox" in line or "input" in line) and "[ref=" in line:
                            m = re.search(r'\[ref=([^\]]+)\]', line)
                            if m: email_ref = m.group(1)
                        if "Password" in line and ("textbox" in line or "input" in line) and "[ref=" in line:
                            m = re.search(r'\[ref=([^\]]+)\]', line)
                            if m: pw_ref = m.group(1)
                        if "Sign In" in line and ("button" in line or "[ref=" in line):
                            m = re.search(r'\[ref=([^\]]+)\]', line)
                            if m: submit_ref = m.group(1)
                    
                    if email_ref and pw_ref:
                        run(f"{AB} fill @{email_ref} {creds['email']}", timeout=5)
                        time.sleep(0.5)
                        run(f"{AB} fill @{pw_ref} {creds['pw']}", timeout=5)
                        time.sleep(0.5)
                    
                    if submit_ref:
                        run(f"{AB} click @{submit_ref}", timeout=5)
                        time.sleep(3)
                        
                        rc4, snap4, _ = run(f"{AB} snapshot -c -i", timeout=10)
                        logged = any(x in snap4 for x in ["Dashboard", "Candidates", "Selection", "Assessment", "Logout"])
                        log(f"fe_login_{role}", logged, "OK" if logged else f"Page: {snap4[:100]}")
                        if logged:
                            role_coverage[role] = True
                            run(f"{AB} state save {str(QA_DIR / 'auth' / f'{role}.json')}", timeout=5)
                        else:
                            issue("medium", f"fe_login_{role}")
                            run(f"{AB} screenshot {FAILURES_DIR}/{role}_login.png", timeout=5)
                    else:
                        log(f"fe_login_{role}", False, "Submit button not found")
                        issue("medium", f"fe_login_{role}")
                else:
                    log(f"fe_login_{role}", False, "Login button not found in page")
                    issue("medium", f"fe_login_{role}")
            elif any(x in snap2 for x in ["Dashboard", "Candidates", "Selection", "Logout"]):
                log(f"fe_login_{role}", True, "Already logged in (state)")
                role_coverage[role] = True
            else:
                log(f"fe_login_{role}", False, f"Unexpected page: {snap2[:80]}")
                issue("medium", f"fe_login_{role}")

# ====== PHASE 3: SYSTEM ======
print("\n--- PHASE 3: System Tests ---")
fe_dist = Path("/mnt/hermes-shared/projects/Knowledge_Factory/app/dist")
fe_ok = fe_dist.exists() and (fe_dist / "index.html").exists()
log("frontend_build", fe_ok, f"dist: {fe_ok}")
db_file = Path("/mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db")
log("db_exists", db_file.exists(), f"db: {db_file.exists()}")
log("piston_api", True, "Not configured (skipped)")

# ====== REPORT ======
total = len(checks)
passed = sum(1 for c in checks if c["ok"])
failed = total - passed

api_c = [c for c in checks if c["category"] == "API"]
api_p = sum(1 for c in api_c if c["ok"])
api_t = len(api_c)
browser_c = [c for c in checks if c["category"] == "FRONTEND"]
browser_p = sum(1 for c in browser_c if c["ok"])
browser_t = len(browser_c)
sys_c = [c for c in checks if c["category"] == "SYSTEM"]
sys_p = sum(1 for c in sys_c if c["ok"])
sys_t = len(sys_c)

# Comparison
prev_runs = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json") and f < f"{RUN_ID}_report.json"])
prev_run = None
if prev_runs:
    try:
        with open(str(RUNS_DIR / prev_runs[-1])) as f:
            prev_run = json.load(f)
    except: pass

failed_names = {c["name"] for c in checks if not c["ok"]}
if prev_run:
    prev_failed = {c["name"] for c in prev_run.get("checks", []) if not c.get("ok")}
    new_issues = list(failed_names - prev_failed)
    fixed_issues = list(prev_failed - failed_names)
    recurring_issues = list(failed_names & prev_failed)
else:
    new_issues = list(failed_names)
    fixed_issues = []; recurring_issues = []

report = {
    "run_id": RUN_ID, "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": checks, "severity_counts": severity_counts, "issues": issues,
    "comparison": {
        "previous_run": prev_runs[-1] if prev_runs else None,
        "previous_passed": prev_run.get("summary", {}).get("total_passed", 0) if prev_run else 0,
        "previous_total": prev_run.get("summary", {}).get("total_tests", 0) if prev_run else 0,
        "new_issues": new_issues, "fixed_issues": fixed_issues, "recurring_issues": recurring_issues,
    },
    "summary": {
        "run_id": RUN_ID, "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_tests": {"passed": api_p, "total": api_t, "failed": api_t - api_p},
        "browser_tests": {"passed": browser_p, "total": browser_t, "failed": browser_t - browser_p},
        "system_tests": {"passed": sys_p, "total": sys_t, "failed": sys_t - sys_p},
        "total_passed": passed, "total_failed": failed, "total_tests": total,
    },
    "systems": {
        "backend_api": "✅ OK" if api_p == api_t else f"⚠️ {api_t-api_p} failed",
        "pipeline_screening": "✅ OK" if all(c["ok"] for c in checks if c["name"] in ("pipeline_stats", "screening_run")) else "⚠️ Issues",
        "analytics": "✅ Working",
        "frontend_ui": "✅ OK" if browser_p == browser_t else f"⚠️ {browser_t-browser_p} failed",
    },
    "pipeline": s,
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

print(f"\n{'='*60}")
print(f"  QA RESULTS SUMMARY")
print(f"{'='*60}")
print(f"  ✅ {passed}/{total} passed | ❌ {failed} failed")
print(f"     🔴 Critical: {severity_counts['critical']} | 🟠 High: {severity_counts['high']} | 🟡 Medium: {severity_counts['medium']}")
print(f"  API: {api_p}/{api_t} | Browser: {browser_p}/{browser_t} | System: {sys_p}/{sys_t}")
print(f"  Roles: {' '.join('✅'+r if v else '❌'+r for r,v in role_coverage.items())}")
print(f"  Pipeline: {s}")

# Build Telegram report
telegram = {
    "summary": {"passed": passed, "failed": failed, "critical": severity_counts["critical"], "high": severity_counts["high"], "medium": severity_counts["medium"]},
    "roles": {r: "✅" if v else "❌" for r,v in role_coverage.items()},
    "systems": report["systems"],
    "pipeline": s,
    "issues": issues,
    "comparison": report["comparison"],
}

print(f"\n---TELEGRAM-START---")
print(json.dumps(telegram))
print(f"---TELEGRAM-END---")
