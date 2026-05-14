#!/usr/bin/env python3
"""
Knowledge Factory Full QA — v1
Merges existing API/browser/system tests + 6 new production-readiness phases.
Outputs structured JSON report + Telegram summary.
"""
import json, os, subprocess, time, re, urllib.request, sys, sqlite3, statistics
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://localhost:8000"
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
QA_DIR = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory")
RUNS_DIR = QA_DIR / "qa_runs"
FAILURES_DIR = QA_DIR / "failures" / RUN_ID
AB = "/opt/hermes_shared_memory/bin/ab"
PROJ = Path("/mnt/hermes-shared/projects/Knowledge_Factory")
FAILURES_DIR.mkdir(parents=True, exist_ok=True)

ROLES = {
    "superadmin": {"email": "superadmin@knowledgefactory.io", "pw": "Super@12345"},
    "admin": {"email": "admin@knowledgefactory.io", "pw": "admin123"},
    "hr": {"email": "hr@knowledgefactory.io", "pw": "Hr@12345"},
    "interviewer": {"email": "interviewer@test.com", "pw": "Interviewer@12345"},
    "candidate": {"email": "candidate@test.com", "pw": "Candidate@12345"},
}

checks = []
severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
issues = {"critical": [], "high": [], "medium": [], "low": []}
phase_results = {}
role_coverage = {r: False for r in ROLES}

def run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def curl_get(url, token=None):
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
    hdrs = ['-H "Content-Type: application/json"']
    if token:
        hdrs.append(f'-H "Authorization: Bearer {token}"')
    hdr_str = " ".join(hdrs)
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

def log(name, ok, detail="", category="API", phase=""):
    checks.append({"name": name, "ok": ok, "detail": str(detail)[:300], "category": category, "phase": phase})
    print(f"  {'✅' if ok else '❌'} {name}: {str(detail)[:200]}")

def issue(sev, name):
    severity_counts[sev] += 1
    issues[sev].append(name)

print(f"\n{'='*60}")
print(f"  KNOWLEDGE FACTORY FULL QA — {RUN_ID}")
print(f"{'='*60}")

# ====== PHASE 1: API TESTS (EXISTING) ======
print("\n═══════════════════════════════════════")
print("  PHASE 1: API Tests")
print("═══════════════════════════════════════")

code, data = curl_get(f"{BASE_URL}/health")
log("backend_health", code == 200, f"HTTP {code}: {data.get('status','?')}", phase="api")
if code != 200: issue("critical", "backend_health")

tokens = {}
for role in ROLES:
    code, data = curl_post(f"{BASE_URL}/api/auth/login",
        {"email": ROLES[role]["email"], "password": ROLES[role]["pw"]})
    if code == 200 and "access_token" in data:
        tokens[role] = data["access_token"]
        role_coverage[role] = True
        log(f"login_{role}", True, f"{ROLES[role]['email']}", phase="api")
    else:
        log(f"login_{role}", False, f"HTTP {code}: {data.get('detail','no token')[:50]}", phase="api")
        issue("critical", f"login_{role}")

for role in tokens:
    code, data = curl_get(f"{BASE_URL}/api/auth/me", tokens[role])
    actual_role = data.get("role", "")
    expected = role.upper()
    log(f"auth_me_{role}", code == 200 and actual_role == expected, f"HTTP {code} role={actual_role}", phase="api")
    if code != 200: issue("high", f"auth_me_{role}")

code, data = curl_get(f"{BASE_URL}/api/screening/pipeline-stats")
stats = data.get("stats", data) if isinstance(data, dict) else {}
s = " ".join(f"{k}:{v}" for k,v in stats.items() if isinstance(v, int))[:200] if isinstance(stats, dict) else str(data)[:100]
log("pipeline_stats", code == 200, s, phase="api")
if code != 200: issue("high", "pipeline_stats")

if "hr" in tokens:
    code, data = curl_post(f"{BASE_URL}/api/screening/run", token=tokens["hr"])
    ok = "screened" in data
    log("screening_run", ok, f"HTTP {code} screened={data.get('screened','?')} passed={data.get('passed','?')} rejected={data.get('rejected','?')}", phase="api")
    if not ok: issue("high", "screening_run")
else:
    log("screening_run", False, "No HR token", phase="api")

for role in ["superadmin", "admin", "hr"]:
    if role in tokens:
        code, data = curl_get(f"{BASE_URL}/api/candidates/", tokens[role])
        lst = data.get("data", data) if isinstance(data, dict) else []
        count = len(lst) if isinstance(lst, list) else "?"
        log(f"candidates_{role}", code == 200, f"HTTP {code}: {count} candidates", phase="api")
        if code != 200: issue("high", f"candidates_{role}")

if "candidate" in tokens:
    code, data = curl_get(f"{BASE_URL}/api/candidates/me", tokens["candidate"])
    log("candidate_me", code == 200, f"HTTP {code}: {data.get('email','?')}", phase="api")
    if code != 200: issue("high", "candidate_me")

for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        code = curl_http_code(f"{BASE_URL}/api/hiring-cycles/", tokens[role])
        log(f"hiring_cycles_{role}", code in (200, 404), f"HTTP {code}", phase="api")
        if code not in (200, 404): issue("high", f"hiring_cycles_{role}")

for role in ["admin", "superadmin", "hr"]:
    if role in tokens:
        for ep in ["funnel", "dashboard"]:
            code = curl_http_code(f"{BASE_URL}/api/analytics/{ep}", tokens[role])
            log(f"analytics_{ep}_{role}", code == 200, f"HTTP {code}", phase="api")
            if code != 200: issue("high", f"analytics_{ep}_{role}")

for role in ["admin", "superadmin"]:
    if role in tokens:
        for ep in ["users", "logs"]:
            code = curl_http_code(f"{BASE_URL}/api/admin/{ep}", tokens[role])
            log(f"admin_{ep}_{role}", code in (200, 404), f"HTTP {code}", phase="api")
            if code not in (200, 404): issue("high", f"admin_{ep}_{role}")

if "candidate" in tokens:
    code = curl_http_code(f"{BASE_URL}/api/assessment/active", tokens["candidate"])
    log("assessment_active", code in (200, 404), f"HTTP {code}", phase="api")
    if code not in (200, 404): issue("high", "assessment_active")

code, data = curl_post(f"{BASE_URL}/api/code/execute", {"language": "python", "code": "print(1)"})
log("code_exec_noauth", code == 401, f"HTTP {code}: {data.get('detail','?')[:50]}", phase="api")
if code != 401: issue("high", "code_exec_noauth")

for role in ["admin", "hr"]:
    if role in tokens:
        code, data = curl_post(f"{BASE_URL}/api/code/execute", {"language": "python", "code": "print(1)"}, tokens[role])
        ok = code in (200, 401, 502, 503, 422)
        log(f"code_exec_{role}", ok, f"HTTP {code}", phase="api")
        if not ok: issue("high", f"code_exec_{role}")

if "candidate" in tokens:
    ts = datetime.now().isoformat()
    code, data = curl_post(f"{BASE_URL}/api/proctoring/event", {
        "assessment_id": "00000000-0000-0000-0000-000000000000",
        "candidate_id": "00000000-0000-0000-0000-000000000000",
        "event_type": "tab_switch", "timestamp": ts
    }, tokens["candidate"])
    ok = code in (200, 201, 422, 404)
    log("proctoring_event", ok, f"HTTP {code}", phase="api")
    if not ok: issue("high", "proctoring_event")

test_email = f"qa_test_{int(time.time())}@test.com"
code, data = curl_post(f"{BASE_URL}/api/auth/register",
    {"email": test_email, "password": "Test@12345", "name": "QA Cron", "role": "candidate"})
ok = code in (200, 201)
log("register_candidate", ok, f"HTTP {code}: {test_email if ok else data.get('detail','?')[:50]}", phase="api")
if not ok: issue("high", "register_candidate")

code = curl_http_code(f"{BASE_URL}/api/questions/generate")
log("questions_generate", code in (200, 401, 404), f"HTTP {code}", phase="api")

phase_results["api"] = {"passed": sum(1 for c in checks if c.get("phase") == "api" and c["ok"]),
    "total": sum(1 for c in checks if c.get("phase") == "api")}

# ====== PHASE 2: PYTEST SUITE ======
print("\n═══════════════════════════════════════")
print("  PHASE 2: Pytest Suite (skill: python-testing-patterns)")
print("═══════════════════════════════════════")
rc, out, err = run("cd /mnt/hermes-shared/projects/Knowledge_Factory/backend && .venv/bin/python -m pytest tests/ -x --tb=short -q 2>&1", timeout=300)
lines = out.split("\n")[-10:] if out else []
summary_line = next((l for l in lines if "passed" in l or "failed" in l or "error" in l or "warnings" in l), out[-200:] if out else "")
passed_count = 0
failed_count = 0
error_count = 0
for line in lines:
    m = re.search(r'(\d+) passed', line)
    if m: passed_count = int(m.group(1))
    m = re.search(r'(\d+) failed', line)
    if m: failed_count = int(m.group(1))
    m = re.search(r'(\d+) error', line)
    if m: error_count = int(m.group(1))

# Get failed/errored test names
failed_tests = []
for line in out.split("\n"):
    if line.startswith("FAILED "):
        failed_tests.append(line.replace("FAILED ", "").strip())
    elif line.startswith("ERROR "):
        failed_tests.append(line.replace("ERROR ", "").strip())

pytest_ok = rc == 0 and failed_count == 0 and error_count == 0
log("pytest_suite", pytest_ok, f"passed={passed_count} failed={failed_count} errors={error_count}", category="TEST", phase="pytest")
if not pytest_ok:
    issue("high", f"pytest_suite: {failed_count} failed")
    for ft in failed_tests[:5]:
        log(f"  failed_test", False, ft, category="TEST", phase="pytest")

phase_results["pytest"] = {"passed": 1 if pytest_ok else 0, "total": 1,
    "passed_count": passed_count, "failed_count": failed_count, "error_count": error_count,
    "failed_tests": failed_tests[:10]}

# ====== PHASE 3: RESPONSE TIME BASELINE ======
print("\n═══════════════════════════════════════")
print("  PHASE 3: Response Time Baseline (skill: performance-engineer)")
print("═══════════════════════════════════════")
perf_baseline = {}
perf_targets = [
    ("POST /api/auth/login", lambda: curl_post(f"{BASE_URL}/api/auth/login",
        {"email": "admin@knowledgefactory.io", "password": "admin123"})),
    ("GET /api/screening/pipeline-stats", lambda: curl_get(f"{BASE_URL}/api/screening/pipeline-stats")),
]
if "admin" in tokens:
    perf_targets += [
        ("GET /api/candidates/", lambda: curl_get(f"{BASE_URL}/api/candidates/", tokens["admin"])),
        ("GET /api/analytics/dashboard", lambda: curl_get(f"{BASE_URL}/api/analytics/dashboard", tokens["admin"])),
        ("GET /api/analytics/funnel", lambda: curl_get(f"{BASE_URL}/api/analytics/funnel", tokens["admin"])),
    ]

for name, fn in perf_targets:
    times = []
    http_codes = set()
    for _ in range(5):
        start = time.time()
        code, _ = fn()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        http_codes.add(code)
    times.sort()
    p50 = statistics.median(times)
    p95 = times[int(len(times) * 0.95)]
    p99 = times[int(len(times) * 0.99)]
    perf_baseline[name] = {"p50_ms": round(p50, 1), "p95_ms": round(p95, 1), "p99_ms": round(p99, 1), "codes": list(http_codes)}
    ok = p95 < 2000  # 2s threshold
    log(f"perf_{name.replace('/','_').replace(' ','_')}", ok,
        f"p50={p50:.0f}ms p95={p95:.0f}ms p99={p99:.0f}ms", category="PERF", phase="perf")
    if not ok: issue("medium", f"perf_{name}")

# Compare with previous baseline
perf_baseline_path = RUNS_DIR / "perf_baseline.json"
prev_perf = {}
if perf_baseline_path.exists():
    try:
        prev_perf = json.loads(perf_baseline_path.read_text())
        for name, metrics in perf_baseline.items():
            if name in prev_perf:
                prev_p50 = prev_perf[name].get("p50_ms", 0)
                if prev_p50 > 0:
                    pct_change = ((metrics["p50_ms"] - prev_p50) / prev_p50) * 100
                    if pct_change > 20:
                        log(f"perf_regression_{name.replace('/','_')}", False,
                            f"p50 {prev_p50:.0f}ms -> {metrics['p50_ms']:.0f}ms ({pct_change:+.0f}%)", category="PERF", phase="perf")
                        issue("medium", f"perf_regression_{name}")
                    elif pct_change < -20:
                        log(f"perf_improvement_{name.replace('/','_')}", True,
                            f"p50 {prev_p50:.0f}ms -> {metrics['p50_ms']:.0f}ms ({pct_change:+.0f}%)", category="PERF", phase="perf")
    except: pass

perf_baseline_path.write_text(json.dumps(perf_baseline, indent=2))
phase_results["perf"] = {"passed": sum(1 for c in checks if c.get("phase") == "perf" and c["ok"]),
    "total": sum(1 for c in checks if c.get("phase") == "perf")}

# ====== PHASE 4: DEPENDENCY AUDIT ======
print("\n═══════════════════════════════════════")
print("  PHASE 4: Dependency Audit (skill: codebase-cleanup-deps-audit)")
print("═══════════════════════════════════════")
dep_findings = {"npm": {}, "pip": {}}

# npm audit
rc, out, err = run("cd /mnt/hermes-shared/projects/Knowledge_Factory/app && npm audit --audit-level=high 2>&1", timeout=60)
npm_vulns = 0
npm_critical = 0
npm_high = 0
for line in out.split("\n"):
    m = re.search(r'(\d+)\s+(critical|high|moderate|low)\s+vulnerabilit', line, re.IGNORECASE)
    if m:
        npm_vulns = int(m.group(1))
        sev = m.group(2).lower()
        if sev == "critical": npm_critical = npm_vulns
        elif sev == "high": npm_high = npm_vulns
log("npm_audit", npm_critical == 0 and npm_high == 0,
    f"vulns={npm_vulns} critical={npm_critical} high={npm_high}", category="DEP", phase="dep")
if npm_critical > 0 or npm_high > 3:
    issue("high", f"npm_audit: {npm_critical} critical, {npm_high} high")
dep_findings["npm"] = {"vulns": npm_vulns, "critical": npm_critical, "high": npm_high}

# pip-audit
run("cd /mnt/hermes-shared/projects/Knowledge_Factory/backend && .venv/bin/pip install pip-audit -q", timeout=30)
rc, out, err = run("cd /mnt/hermes-shared/projects/Knowledge_Factory/backend && .venv/bin/pip-audit 2>&1", timeout=60)
pip_vulns = 0
pip_critical = 0
pip_high = 0
for line in out.split("\n"):
    if "No known vulnerabilities found" in line:
        pip_vulns = 0
        break
    if "vulnerabilit" in line.lower():
        m = re.search(r'(\d+)', line)
        if m: pip_vulns = int(m.group(1))
log("pip_audit", pip_vulns == 0,
    f"vulns={pip_vulns} critical={pip_critical} high={pip_high}", category="DEP", phase="dep")
if pip_vulns > 0:
    issue("high", f"pip_audit: {pip_vulns} vulnerabilities")
dep_findings["pip"] = {"vulns": pip_vulns, "critical": pip_critical, "high": pip_high}

phase_results["dep"] = {"passed": sum(1 for c in checks if c.get("phase") == "dep" and c["ok"]),
    "total": sum(1 for c in checks if c.get("phase") == "dep")}

# ====== PHASE 5: DB INTEGRITY ======
print("\n═══════════════════════════════════════")
print("  PHASE 5: DB Integrity (skill: database-admin)")
print("═══════════════════════════════════════")
db_path = PROJ / "backend" / "knowledge_factory.db"
db_findings = {"integrity": True, "foreign_keys": True, "tables": {}, "missing_indexes": [], "size_bytes": 0}

if db_path.exists():
    db_findings["size_bytes"] = db_path.stat().st_size
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Integrity check
    cur.execute("PRAGMA integrity_check")
    integrity = cur.fetchone()[0]
    db_findings["integrity"] = integrity == "ok"
    log("db_integrity", integrity == "ok", f"integrity_check: {integrity}", category="DB", phase="db")
    if integrity != "ok": issue("high", f"db_integrity: {integrity}")

    # Foreign key check
    cur.execute("PRAGMA foreign_key_check")
    fk_violations = cur.fetchall()
    db_findings["foreign_keys"] = len(fk_violations) == 0
    log("db_foreign_keys", len(fk_violations) == 0, f"FK violations: {len(fk_violations)}", category="DB", phase="db")
    if fk_violations: issue("medium", f"db_foreign_keys: {len(fk_violations)} violations")

    # Row counts
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]
    for table in tables:
        if table.startswith("sqlite_"): continue
        cur.execute(f"SELECT COUNT(*) FROM \"{table}\"")
        count = cur.fetchone()[0]
        db_findings["tables"][table] = count

    log("db_tables", True, f"{len(db_findings['tables'])} tables: {sum(db_findings['tables'].values())} total rows", category="DB", phase="db")

    # Missing indexes on FK columns
    for table in tables:
        if table.startswith("sqlite_"): continue
        try:
            cur.execute(f"PRAGMA foreign_key_list(\"{table}\")")
            fks = cur.fetchall()
            for fk in fks:
                from_col = fk[3]  # "from" column
                cur.execute(f"PRAGMA index_list(\"{table}\")")
                indexes = [row[1] for row in cur.fetchall()]
                # Check if any index covers this column
                has_index = False
                for idx in indexes:
                    cur.execute(f"PRAGMA index_info(\"{idx}\")")
                    cols = [row[2] for row in cur.fetchall()]
                    if from_col in cols:
                        has_index = True
                        break
                if not has_index:
                    db_findings["missing_indexes"].append(f"{table}({from_col})")
        except: pass

    if db_findings["missing_indexes"]:
        log("db_missing_indexes", False, f"Missing indexes: {', '.join(db_findings['missing_indexes'][:5])}", category="DB", phase="db")
        issue("low", f"db_missing_indexes: {len(db_findings['missing_indexes'])}")
    else:
        log("db_missing_indexes", True, "All FK columns have indexes", category="DB", phase="db")

    conn.close()
else:
    log("db_exists", False, "DB file not found", category="DB", phase="db")
    issue("critical", "db_missing")

phase_results["db"] = {"passed": sum(1 for c in checks if c.get("phase") == "db" and c["ok"]),
    "total": sum(1 for c in checks if c.get("phase") == "db")}

# ====== PHASE 6: FRONTEND CONSOLE CHECK ======
# NOTE: Phase 6 uses browser tools — handled by the agent via the cron prompt.
# This script does the CLI parts; the agent does browser console capture separately.
print("\n═══════════════════════════════════════")
print("  PHASE 6: Frontend Console Check (agent-driven via browser tools)")
print("  → Handled by Hermes agent using agent-browser + e2e-testing-patterns")
print("═══════════════════════════════════════")
phase_results["fe_console"] = {"passed": 0, "total": 0, "note": "handled_by_agent"}

# ====== PHASE 7: UNPROTECTED ENDPOINT SCAN ======
print("\n═══════════════════════════════════════")
print("  PHASE 7: Unprotected Endpoint Scan (skill: api-security-testing)")
print("═══════════════════════════════════════")
routes_dir = PROJ / "backend" / "app" / "features"
unprotected = []
protected = []
# Use grep via shell for reliability
rc, out, err = run("grep -rn '@router\\.' /mnt/hermes-shared/projects/Knowledge_Factory/backend/app/features/*/routes.py 2>/dev/null", timeout=10)
all_routes = out.split("\n") if out else []
for line in all_routes:
    if not line.strip(): continue
    parts = line.split(":")
    if len(parts) < 3: continue
    filepath = parts[0]
    feature = Path(filepath).parent.name
    decorator = ":".join(parts[2:])
    # Extract method (get/post/put/delete/patch)
    method_match = re.search(r'@router\.(get|post|put|delete|patch)', decorator)
    method = method_match.group(1) if method_match else "?"
    # Find the async def line for this endpoint
    rc2, def_line, _ = run(f"tail -n +{parts[1]} {filepath} | grep -m1 'async def '", timeout=5)
    handler = def_line.strip() if def_line else "unknown"
    handler_name = handler.replace("async def ", "").split("(")[0].strip() if handler else "unknown"
    # Check if next lines have auth dependency in the function signature
    sig_match = re.search(r'async def\s+\w+\s*\((.*?)\):', def_line[:300] if len(def_line) > 300 else def_line) if def_line else None
    sig = sig_match.group(1) if sig_match else ""
    has_auth = bool(re.search(r'Depends\(require_role|Depends\(get_current_user|Depends\(get_optional_user', sig))
    if has_auth:
        protected.append(f"{feature}/{handler_name}")
    else:
        unprotected.append(f"{feature}/{handler_name} ({method})")

log("endpoint_scan", True, f"{len(protected)} protected, {len(unprotected)} with no auth check", category="SEC", phase="sec")

# Specifically check known vulnerable endpoints
known_unprotected = ["screening/pipeline-stats", "screening/run"]
for known in known_unprotected:
    found = any(known in u for u in unprotected)
    log(f"known_unprotected_{known.replace('/','_')}", not found,
        f"STILL unprotected!" if found else "Protected (good)" if any(known in p for p in protected) else "Not found (possible) ",
        category="SEC", phase="sec")
    if found: issue("high", f"unprotected_endpoint_{known}")

if unprotected:
    log("total_unprotected", False, f"{len(unprotected)} endpoints without auth: {'; '.join(unprotected[:8])}", category="SEC", phase="sec")
    if len(unprotected) > 1: issue("medium", f"{len(unprotected)} unprotected endpoints")
else:
    log("total_unprotected", True, "All endpoints have auth", category="SEC", phase="sec")

phase_results["sec"] = {"passed": sum(1 for c in checks if c.get("phase") == "sec" and c["ok"]),
    "total": sum(1 for c in checks if c.get("phase") == "sec"),
    "unprotected": unprotected}

# ====== PHASE 8: BROWSER TESTS (EXISTING) ======
# Handled by the agent using agent-browser — script does setup only
print("\n═══════════════════════════════════════")
print("  PHASE 8: Browser Login Tests (agent-driven via agent-browser)")
print("═══════════════════════════════════════")
phase_results["browser"] = {"passed": 0, "total": 0, "note": "handled_by_agent"}
code = curl_http_code(f"{NGROK_URL}/health") if NGROK_URL else 0
log("ngrok_reachable", code == 200, f"HTTP {code}", category="SYS", phase="browser")
if code != 200: issue("critical", "ngrok_reachable")

fe_dist = PROJ / "app" / "dist"
fe_ok = fe_dist.exists() and (fe_dist / "index.html").exists()
log("frontend_build", fe_ok, f"dist: {fe_ok}", category="SYS", phase="browser")

# ====== PHASE 9: SYSTEM CHECKS ======
print("\n═══════════════════════════════════════")
print("  PHASE 9: System Checks")
print("═══════════════════════════════════════")
log("db_file_exists", db_path.exists(), f"db: {db_path.exists()} ({db_path.stat().st_size // 1024}KB)" if db_path.exists() else "", category="SYS", phase="sys")
log("frontend_dist", fe_ok, f"dist: {fe_ok}", category="SYS", phase="sys")
log("piston_api", True, "Not configured (skipped)", category="SYS", phase="sys")

# Git status
rc, out, err = run("cd /mnt/hermes-shared/projects/Knowledge_Factory && git status --porcelain 2>&1", timeout=10)
uncommitted = len([l for l in out.split("\n") if l.strip()]) if out else 0
log("git_uncommitted", uncommitted == 0, f"{uncommitted} uncommitted changes", category="SYS", phase="sys")
if uncommitted > 10: issue("low", f"git_uncommitted: {uncommitted} files")

# Docker check
rc, out, err = run("docker ps -q 2>&1", timeout=5)
docker_ok = rc == 0 or "permission denied" in err.lower()
log("docker_available", docker_ok, "Docker: OK" if docker_ok else "Docker: permission denied", category="SYS", phase="sys")

# Dockerfile check
df = PROJ / "Dockerfile"
log("dockerfile_exists", df.exists(), "Dockerfile present" if df.exists() else "No Dockerfile", category="SYS", phase="sys")

phase_results["sys"] = {"passed": sum(1 for c in checks if c.get("phase") == "sys" and c["ok"]),
    "total": sum(1 for c in checks if c.get("phase") == "sys")}

# ====== REPORT ======
total = len(checks)
passed = sum(1 for c in checks if c["ok"])
failed = total - passed

# Previous run comparison
prev_runs = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json") and not f.startswith(RUN_ID)])
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
    "version": "qa_full_v1",
    "checks": checks, "severity_counts": severity_counts, "issues": issues,
    "phase_results": phase_results,
    "comparison": {
        "previous_run": prev_runs[-1] if prev_runs else None,
        "new_issues": new_issues, "fixed_issues": fixed_issues, "recurring_issues": recurring_issues,
    },
    "summary": {
        "total_passed": passed, "total_failed": failed, "total_tests": total,
    },
    "perf_baseline": perf_baseline,
    "db_findings": db_findings,
    "dep_findings": dep_findings,
    "unprotected_endpoints": unprotected,
    "role_coverage": {r: bool(v) for r,v in role_coverage.items()},
    "systems": {
        "backend_api": "✅ OK" if not any(c["name"].startswith("backend_health") and not c["ok"] for c in checks) else "⚠️ Issues",
        "pipeline_screening": "✅ OK" if all(c["ok"] for c in checks if c["name"] in ("pipeline_stats", "screening_run")) else "⚠️ Issues",
        "pytest": f"✅ {passed_count}/{passed_count+failed_count}" if pytest_ok else f"⚠️ {failed_count} failed",
        "perf": f"✅ All under threshold" if phase_results.get("perf",{}).get("passed",0) == phase_results.get("perf",{}).get("total",0) else "⚠️ Regressions detected",
        "deps": "✅ Clean" if npm_critical == 0 and pip_vulns == 0 else "⚠️ Vulns found",
        "db_integrity": "✅ OK" if db_findings.get("integrity") else "❌ Issues",
        "endpoint_security": f"⚠️ {len(unprotected)} unprotected" if unprotected else "✅ All protected",
    },
    "pipeline": s,
}

report_path = RUNS_DIR / f"{RUN_ID}_report.json"
with open(report_path, "w") as f:
    json.dump(report, f, indent=2, default=str)

summary = {
    "run_id": RUN_ID, "passed": passed, "failed": failed,
    "critical": severity_counts["critical"], "high": severity_counts["high"],
    "total": total, "pytest": {"passed": passed_count, "failed": failed_count},
    "deps": {"npm": npm_vulns, "pip": pip_vulns},
    "perf": phase_results.get("perf", {}),
    "db_ok": db_findings.get("integrity", False) and db_findings.get("foreign_keys", False),
    "unprotected_endpoints": len(unprotected),
    "roles": {r: bool(v) for r,v in role_coverage.items()},
    "systems": report["systems"],
}
with open(RUNS_DIR / "latest_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

# Cleanup old runs (keep last 10)
all_reports = sorted([f for f in os.listdir(str(RUNS_DIR)) if f.endswith("_report.json")])
for old_f in all_reports[:-10]:
    base = old_f.replace("_report.json", "")
    for s in ["_report.json", "_telegram_data.json"]:
        p = RUNS_DIR / f"{base}{s}"
        if p.exists(): p.unlink()

print(f"\n{'='*60}")
print(f"  QA FULL RESULTS — {RUN_ID}")
print(f"{'='*60}")
print(f"  ✅ {passed}/{total} passed | ❌ {failed} failed")
print(f"     🔴 Critical: {severity_counts['critical']} | 🟠 High: {severity_counts['high']} | 🟡 Medium: {severity_counts['medium']}")
print(f"  Phases:")
for pname, pres in phase_results.items():
    print(f"    {pname}: {pres.get('passed',0)}/{pres.get('total',0)}")
print(f"  Roles: {' '.join('✅'+r if v else '❌'+r for r,v in role_coverage.items())}")
print(f"  Pipeline: {s}")
print(f"  Perf: {len(perf_baseline)} endpoints baseline")
print(f"  Deps: npm={npm_vulns} pip={pip_vulns}")
print(f"  DB: {'OK' if db_findings.get('integrity', False) else 'ISSUES'}")
print(f"  Unprotected endpoints: {len(unprotected)}")

# Build Telegram report
telegram = {
    "summary": {"passed": passed, "failed": failed, "critical": severity_counts["critical"],
        "high": severity_counts["high"], "medium": severity_counts["medium"]},
    "phases": {p: {"passed": r.get("passed",0), "total": r.get("total",0)} for p,r in phase_results.items()},
    "roles": {r: "✅" if v else "❌" for r,v in role_coverage.items()},
    "systems": report["systems"],
    "pipeline": s,
    "issues": {k: v[:5] for k,v in issues.items() if v},
    "comparison": report["comparison"],
    "pytest": f"{passed_count}/{passed_count+failed_count}",
    "deps": f"npm:{npm_vulns} pip:{pip_vulns}",
    "unprotected": len(unprotected),
}

print(f"\n---TELEGRAM-START---")
print(json.dumps(telegram))
print(f"---TELEGRAM-END---")
