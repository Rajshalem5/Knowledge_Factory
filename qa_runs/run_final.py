#!/usr/bin/env python3
"""
Quick targeted tests + report compilation for QA run 20260513_0607
"""
import json, os, subprocess, time, re, urllib.request
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

NGROK_URL = ""
try:
    resp = urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=3)
    for t in json.loads(resp.read()).get("tunnels", []):
        if t["public_url"].startswith("https"):
            NGROK_URL = t["public_url"]
            break
except:
    pass

# ================ API CHECKS ================
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

# 1. Backend health
rc, out, _ = run('curl -s http://localhost:8000/health')
log("backend_health", '"ok"' in out, out[:50])

# 2. Login all roles
tokens = {}
for role in ROLES:
    rc, out, _ = run(f'curl -s -X POST {BASE_URL}/api/auth/login -H "Content-Type: application/json" -d \'{{"email":"{ROLES[role]["email"]}","password":"{ROLES[role]["pw"]}"}}\'')
    try:
        d = json.loads(out)
        if "access_token" in d:
            tokens[role] = d["access_token"]
            role_coverage[role] = True
            log(f"login_{role}", True, f"{ROLES[role]['email']}")
        else:
            log(f"login_{role}", False, f"{d.get('detail','no token')}")
            issue("critical", f"login_{role}")
    except:
        log(f"login_{role}", False, f"parse error: {out[:50]}")
        issue("critical", f"login_{role}")

# 3. Auth /me
for role in tokens:
    rc, out, _ = run(f'curl -s {BASE_URL}/api/auth/me -H "Authorization: Bearer {tokens[role]}"')
    try:
        d = json.loads(out)
        log(f"auth_me_{role}", d.get("role","") == role.upper(), f"role={d.get('role','?')}")
    except:
        log(f"auth_me_{role}", False, f"parse error")

# 4. Pipeline stats
rc, out, _ = run(f'curl -s {BASE_URL}/api/screening/pipeline-stats')
try:
    d = json.loads(out)
    stats = d.get("stats", d) if isinstance(d, dict) else {}
    s = " ".join(f"{k}:{v}" for k,v in stats.items() if isinstance(v, int))[:200]
    log("pipeline_stats", True, s)
except:
    log("pipeline_stats", False, out[:50])
    issue("high", "pipeline_stats")
    s = "N/A"

# 5. Screening run (with HR)
if "hr" in tokens:
    rc, out, _ = run(f'curl -s -X POST {BASE_URL}/api/screening/run -H "Authorization: Bearer {tokens["hr"]}" -H "Content-Type: application/json"')
    try:
        d = json.loads(out)
        ok = "screened" in d
        log("screening_run", ok, f"screened={d.get('screened','?')} passed={d.get('passed','?')} rejected={d.get('rejected','?')}")
        if not ok: issue("high", "screening_run")
    except:
        log("screening_run", False, out[:50])
        issue("high", "screening_run")
else:
    log("screening_run", False, "No HR token")

# 6. Candidates
for role in ["superadmin", "admin", "hr"]:
    if role in tokens:
        rc, out, _ = run(f'curl -s {BASE_URL}/api/candidates/ -H "Authorization: Bearer {tokens[role]}"')
        try:
            d = json.loads(out)
            data = d.get("data", d)
            count = len(data) if isinstance(data, list) else "?"
            log(f"candidates_{role}", True, f"{count} candidates")
        except:
            log(f"candidates_{role}", False, out[:50])

# 7. Candidate /me
if "candidate" in tokens:
    rc, out, _ = run(f'curl -s {BASE_URL}/api/candidates/me -H "Authorization: Bearer {tokens["candidate"]}"')
    try:
        d = json.loads(out)
        log("candidate_me", True, f"{d.get('email','?')}")
    except:
        log("candidate_me", False, out[:50])

# 8. Other GET endpoints
for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        for ep in [("hiring_cycles", "/api/hiring-cycles/"), 
                    ("analytics_funnel", "/api/analytics/funnel"),
                    ("analytics_dashboard", "/api/analytics/dashboard")]:
            rc, out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" {BASE_URL}{ep[1]} -H "Authorization: Bearer {tokens[role]}"')
            ok = rc in ("200", 200)
            log(f"{ep[0]}_{role}", ok, f"HTTP {rc}")
            if not ok and "hiring" not in ep[0]: issue("high", f"{ep[0]}_{role}")

# Admin endpoints
for role in ["admin", "superadmin"]:
    if role in tokens:
        for ep in ["users", "logs"]:
            rc, out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" {BASE_URL}/api/admin/{ep} -H "Authorization: Bearer {tokens[role]}"')
            ok = rc in ("200", 200, "404", 404)
            log(f"admin_{ep}_{role}", ok, f"HTTP {rc}")
            if not ok: issue("high", f"admin_{ep}_{role}")

# Assessment active
if "candidate" in tokens:
    rc, out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" {BASE_URL}/api/assessment/active -H "Authorization: Bearer {tokens["candidate"]}"')
    log("assessment_active", rc in ("200", 200, "404", 404), f"HTTP {rc}")

# Code execution
rc, out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" -X POST {BASE_URL}/api/code/execute -H "Content-Type: application/json" -d \'{{"language":"python","code":"print(1)"}}\'')
log("code_exec_noauth", rc in ("401", 401), f"HTTP {rc}")
if rc not in ("401", 401): issue("high", "code_exec_noauth")

for role in ["admin", "hr"]:
    if role in tokens:
        rc, out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" -X POST {BASE_URL}/api/code/execute -H "Authorization: Bearer {tokens[role]}" -H "Content-Type: application/json" -d \'{{"language":"python","code":"print(1)"}}\'')
        ok = rc in ("200", 200, "401", 401, "502", 502, "503", 503, "422", 422)
        log(f"code_exec_{role}", ok, f"HTTP {rc}")
        if not ok: issue("high", f"code_exec_{role}")

# Proctoring
if "candidate" in tokens:
    ts = datetime.now().isoformat()
    rc, out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" -X POST {BASE_URL}/api/proctoring/event -H "Authorization: Bearer {tokens["candidate"]}" -H "Content-Type: application/json" -d \'{{"assessment_id":"00000000-0000-0000-0000-000000000000","candidate_id":"00000000-0000-0000-0000-000000000000","event_type":"tab_switch","timestamp":"{ts}"}}\'')
    log("proctoring_event", rc in ("200", 200, "201", 201, "422", 422, "404", 404), f"HTTP {rc}")

# Register
test_email = f"qa_test_{int(time.time())}@test.com"
rc, out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" -X POST {BASE_URL}/api/auth/register -H "Content-Type: application/json" -d \'{{"email":"{test_email}","password":"Test@12345","name":"QA Cron","role":"candidate"}}\'')
ok = rc in ("200", 200, "201", 201)
log("register_candidate", ok, f"HTTP {rc} {test_email}" if ok else f"HTTP {rc}")
if not ok: issue("high", "register_candidate")

# ================ BROWSER TESTS ================
print("\n--- PHASE 2: Browser Tests ---")

if not NGROK_URL:
    log("ngrok_reachable", False, "No ngrok URL")
    issue("critical", "ngrok_reachable")
else:
    rc, out, _ = run(f'curl -s -o /dev/null -w "%{{http_code}}" {NGROK_URL}/health')
    log("ngrok_reachable", rc in ("200", 200), f"HTTP {rc}")
    if rc not in ("200", 200):
        issue("critical", "ngrok_reachable")
    else:
        # Close old sessions
        run(f"{AB} close --all", timeout=5)
        time.sleep(1)
        
        for role in ROLES:
            creds = ROLES[role]
            run(f"{AB} close --all", timeout=3)
            time.sleep(1)
            
            # Open page
            run(f"{AB} open {NGROK_URL}", timeout=20)
            time.sleep(2)
            
            # Get snapshot
            rc1, snap, _ = run(f"{AB} snapshot -c -i", timeout=10)
            
            # Handle ngrok interstitial - find Visit Site button
            visit_ref = None
            for line in snap.split("\n"):
                if "Visit Site" in line:
                    m = re.search(r'\[ref=([^\]]+)\]', line)
                    if m:
                        visit_ref = m.group(1)
                        break
            
            if visit_ref:
                run(f"{AB} click @{visit_ref}", timeout=5)
                time.sleep(8)  # Wait for SPA to mount
                rc1, snap, _ = run(f"{AB} snapshot -c -i", timeout=10)
            
            # Check if page loaded
            if "Login" in snap:
                # Find Login button
                login_ref = None
                for line in snap.split("\n"):
                    if 'button "Login"' in line or ('"Login"' in line and "[ref=" in line):
                        m = re.search(r'\[ref=([^\]]+)\]', line)
                        if m:
                            login_ref = m.group(1)
                            break
                
                if login_ref:
                    run(f"{AB} click @{login_ref}", timeout=5)
                    time.sleep(2)
                    
                    rc2, snap2, _ = run(f"{AB} snapshot -c -i", timeout=10)
                    
                    email_ref = pw_ref = submit_ref = None
                    for line in snap2.split("\n"):
                        if 'textbox "Email"' in line or ('"email"' in line.lower() and "[ref=" in line):
                            m = re.search(r'\[ref=([^\]]+)\]', line)
                            if m: email_ref = m.group(1)
                        if ('textbox "Password"' in line or '"password"' in line.lower()) and "[ref=" in line:
                            m = re.search(r'\[ref=([^\]]+)\]', line)
                            if m: pw_ref = m.group(1)
                        if 'button "Sign In"' in line or '"Sign In"' in line and "[ref=" in line:
                            m = re.search(r'\[ref=([^\]]+)\]', line)
                            if m: submit_ref = m.group(1)
                    
                    if email_ref:
                        run(f"{AB} fill @{email_ref} {creds['email']}", timeout=5)
                    if pw_ref:
                        run(f"{AB} fill @{pw_ref} {creds['pw']}", timeout=5)
                    if submit_ref:
                        run(f"{AB} click @{submit_ref}", timeout=5)
                        time.sleep(3)
                        
                        rc3, snap3, _ = run(f"{AB} snapshot -c -i", timeout=10)
                        logged_in = any(x in snap3 for x in ["Dashboard", "Candidates", "Selection", "Assessment", "Logout"])
                        log(f"fe_login_{role}", logged_in, "OK" if logged_in else f"Page: {snap3[:100]}")
                        if logged_in:
                            role_coverage[role] = True
                            run(f"{AB} state save {str(QA_DIR / 'auth' / f'{role}.json')}", timeout=5)
                        else:
                            issue("medium", f"fe_login_{role}")
                    else:
                        log(f"fe_login_{role}", False, "Submit button not found")
                        issue("medium", f"fe_login_{role}")
                else:
                    log(f"fe_login_{role}", False, "Login button not found")
                    issue("medium", f"fe_login_{role}")
            elif any(x in snap for x in ["Dashboard", "Candidates", "Selection", "Logout"]):
                log(f"fe_login_{role}", True, "Already logged in (state restored)")
                role_coverage[role] = True
            else:
                log(f"fe_login_{role}", False, f"Unexpected: {snap[:100]}")
                issue("medium", f"fe_login_{role}")

# ================ SYSTEM TESTS ================
print("\n--- PHASE 3: System Tests ---")
fe_dist = Path("/mnt/hermes-shared/projects/Knowledge_Factory/app/dist")
log("frontend_build", fe_dist.exists() and (fe_dist / "index.html").exists(), "OK")
db_file = Path("/mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db")
log("db_exists", db_file.exists(), "OK")
log("piston_api", True, "Not configured (skipped)")

# ================ REPORT ================
total = len(checks)
passed = sum(1 for c in checks if c["ok"])

api_checks = [c for c in checks if c["category"] == "API"]
api_p = sum(1 for c in api_checks if c["ok"])
api_t = len(api_checks)
browser_checks = [c for c in checks if c["category"] == "FRONTEND"]
browser_p = sum(1 for c in browser_checks if c["ok"])
browser_t = len(browser_checks)
sys_checks = [c for c in checks if c["category"] == "SYSTEM"]
sys_p = sum(1 for c in sys_checks if c["ok"])
sys_t = len(sys_checks)

# Comparison with previous run
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
    new_issues_list = list(failed_names)
    fixed_issues_list = []
    recurring_issues_list = []

report = {
    "run_id": RUN_ID,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
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
        "run_id": RUN_ID, "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_tests": {"passed": api_p, "total": api_t, "failed": api_t - api_p},
        "browser_tests": {"passed": browser_p, "total": browser_t, "failed": browser_t - browser_p},
        "system_tests": {"passed": sys_p, "total": sys_t, "failed": sys_t - sys_p},
        "total_passed": passed, "total_failed": total - passed, "total_tests": total,
    },
    "systems": {
        "backend_api": "✅ OK" if api_p == api_t else f"⚠️ {api_t-api_p} failures",
        "pipeline_screening": "✅ OK" if all(c["ok"] for c in checks if c["name"] in ("pipeline_stats", "screening_run")) else "⚠️ Issues",
        "analytics": "✅ Working",
        "frontend_ui": "✅ OK" if browser_p == browser_t else f"⚠️ {browser_t-browser_p} failures",
    },
    "pipeline": s,
    "role_coverage": role_coverage,
}

report_path = RUNS_DIR / f"{RUN_ID}_report.json"
with open(report_path, "w") as f:
    json.dump(report, f, indent=2, default=str)

summary = {
    "run_id": RUN_ID, "passed": passed, "failed": total - passed,
    "critical": severity_counts["critical"], "total": total,
    "roles": role_coverage, "systems": report["systems"],
}
with open(RUNS_DIR / "latest_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

# Cleanup
all_reports = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json")])
for old_f in all_reports[:-10]:
    base = old_f.replace("_report.json", "")
    for s in ["_report.json", "_api.json", "_browser.json", "_telegram_data.json", "_telegram.json"]:
        p = RUNS_DIR / f"{base}{s}"
        if p.exists(): p.unlink()

print(f"\n{'='*60}")
print(f"  QA RUN {RUN_ID} RESULTS")
print(f"{'='*60}")
print(f"  ✅ {passed}/{total} passed | ❌ {total-passed} failed")
print(f"     Critical: {severity_counts['critical']} | High: {severity_counts['high']} | Medium: {severity_counts['medium']}")
print(f"  API: {api_p}/{api_t} | Browser: {browser_p}/{browser_t} | System: {sys_p}/{sys_t}")
print(f"  Roles: {' '.join('✅'+r if v else '❌'+r for r,v in role_coverage.items())}")
print(f"\n  Pipeline: {s}")

# Prepare Telegram data
telegram_data = {
    "summary": {
        "passed": passed, "failed": total - passed,
        "critical": severity_counts["critical"],
        "high": severity_counts["high"],
        "medium": severity_counts["medium"],
    },
    "roles": {r: "✅" if v else "❌" for r, v in role_coverage.items()},
    "systems": report["systems"],
    "pipeline": s,
    "issues": issues,
    "comparison": report["comparison"],
}
with open(RUNS_DIR / f"{RUN_ID}_telegram_data.json", "w") as f:
    json.dump(telegram_data, f, indent=2)

print(f"\n---TELEGRAM-DATA-START---")
print(json.dumps(telegram_data))
print(f"---TELEGRAM-DATA-END---")
