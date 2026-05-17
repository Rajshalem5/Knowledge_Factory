#!/usr/bin/env python3
"""Comprehensive QA cron test for Knowledge Factory - API level tests."""
import json
import sys
import os
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = os.environ.get("BASE_URL", "https://ila-sturdiest-oversentimentally.ngrok-free.dev")
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT = {
    "run_id": RUN_ID,
    "timestamp": datetime.now().isoformat(),
    "summary": {"passed": 0, "failed": 0, "warnings": 0},
    "checks": [],
    "failures": [],
    "fixed": [],
    "systems": {}
}

BASE_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory"

def log_result(name, status, detail=None, severity="MEDIUM"):
    """Log a check result."""
    entry = {"name": name, "status": status, "severity": severity, "detail": detail}
    REPORT["checks"].append(entry)
    if status == "PASS":
        REPORT["summary"]["passed"] += 1
    elif status == "FAIL":
        REPORT["summary"]["failed"] += 1
        REPORT["failures"].append(entry)
    elif status == "WARN":
        REPORT["summary"]["warnings"] += 1

def api_get(path, headers=None, expect_status=200):
    """Make a GET request to the API."""
    url = f"{BASE_URL}{path}"
    req = Request(url, method="GET")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    req.add_header("Accept", "application/json")
    try:
        resp = urlopen(req, timeout=15)
        body = resp.read().decode()
        if resp.status != expect_status:
            return None, f"Expected status {expect_status}, got {resp.status}: {body[:200]}"
        try:
            return json.loads(body), None
        except json.JSONDecodeError:
            return body, None
    except HTTPError as e:
        body = e.read().decode()[:200]
        if e.code == expect_status:
            try:
                return json.loads(body), None
            except json.JSONDecodeError:
                return body, None
        return None, f"HTTP {e.code}: {body}"
    except URLError as e:
        return None, f"Connection failed: {e.reason}"
    except Exception as e:
        return None, str(e)

def api_post(path, data=None, headers=None, expect_status=200):
    """Make a POST request to the API."""
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data else b"{}"
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        resp = urlopen(req, timeout=15)
        rbody = resp.read().decode()
        if resp.status != expect_status:
            return None, f"Expected status {expect_status}, got {resp.status}: {rbody[:200]}"
        try:
            return json.loads(rbody), None
        except json.JSONDecodeError:
            return rbody, None
    except HTTPError as e:
        body = e.read().decode()[:200]
        if e.code == expect_status:
            try:
                return json.loads(body), None
            except json.JSONDecodeError:
                return body, None
        return None, f"HTTP {e.code}: {body}"
    except URLError as e:
        return None, f"Connection failed: {e.reason}"
    except Exception as e:
        return None, str(e)

def login(email, password):
    """Login and return token."""
    data, err = api_post("/api/auth/login", {"email": email, "password": password})
    if err:
        return None, err
    if isinstance(data, dict):
        token = data.get("access_token") or data.get("token") or data.get("data", {}).get("access_token")
        if token:
            return token, None
    return None, f"Login response missing token: {str(data)[:200]}"

# ===== TESTS =====

def test_health():
    """Test health endpoint."""
    data, err = api_get("/health")
    if err:
        log_result("Health Check", "FAIL", err, "CRITICAL")
        return False
    status = data.get("status") if isinstance(data, dict) else str(data)
    if status == "ok":
        log_result("Health Check", "PASS", "Backend healthy")
        return True
    else:
        log_result("Health Check", "FAIL", f"Unexpected health status: {status}", "CRITICAL")
        return False

def test_logins():
    """Test login for all roles."""
    credentials = [
        ("superadmin@knowledgefactory.io", "Super@12345", "Super Admin"),
        ("admin@knowledgefactory.io", "admin123", "Admin"),
        ("hr@test.com", "Hr@12345", "HR"),
        ("interviewer@test.com", "Interviewer@12345", "Interviewer"),
        ("candidate@test.com", "Candidate@12345", "Candidate"),
    ]
    tokens = {}
    all_ok = True
    for email, pw, label in credentials:
        token, err = login(email, pw)
        if token:
            tokens[label] = token
            log_result(f"Login: {label}", "PASS", f"{email} logged in successfully")
        else:
            log_result(f"Login: {label}", "FAIL", err, "CRITICAL")
            all_ok = False
    return tokens, all_ok

def test_admin_endpoints(tokens):
    """Test admin-only endpoints."""
    # Need super admin or admin token
    token = tokens.get("Super Admin") or tokens.get("Admin")
    if not token:
        log_result("Admin Endpoints", "SKIP", "No admin token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test admin users endpoint
    data, err = api_get("/api/admin/users", headers)
    if err:
        log_result("Admin: List Users", "FAIL", err, "HIGH")
    elif isinstance(data, dict) and data.get("data"):
        log_result("Admin: List Users", "PASS", f"Found {len(data['data'])} users")
    elif isinstance(data, list):
        log_result("Admin: List Users", "PASS", f"Found {len(data)} users")
    else:
        log_result("Admin: List Users", "WARN", f"Unexpected response: {str(data)[:200]}")
    
    # Test admin logs
    data, err = api_get("/api/admin/logs", headers)
    if err:
        log_result("Admin: Audit Logs", "FAIL", err, "HIGH")
    else:
        log_result("Admin: Audit Logs", "PASS", "Audit logs accessible")

def test_hr_endpoints(tokens):
    """Test HR-only endpoints."""
    token = tokens.get("HR") or tokens.get("Super Admin") or tokens.get("Admin")
    if not token:
        log_result("HR Endpoints", "SKIP", "No HR token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test candidates list
    data, err = api_get("/api/candidates/", headers)
    if err:
        log_result("HR: List Candidates", "FAIL", err, "HIGH")
    elif isinstance(data, dict):
        candidates = data.get("data", [])
        total = data.get("total", len(candidates))
        log_result("HR: List Candidates", "PASS", f"Found {total} candidates")
    elif isinstance(data, list):
        log_result("HR: List Candidates", "PASS", f"Found {len(data)} candidates")
    else:
        log_result("HR: List Candidates", "WARN", f"Unexpected response: {str(data)[:200]}")
    
    # Test pipeline stats
    data, err = api_get("/api/screening/pipeline-stats")
    if err:
        log_result("HR: Pipeline Stats", "FAIL", err, "HIGH")
    elif isinstance(data, dict):
        stats = data.get("data", data)
        log_result("HR: Pipeline Stats", "PASS", f"Pipeline stats: {str(stats)[:200]}")
    else:
        log_result("HR: Pipeline Stats", "WARN", f"Unexpected: {str(data)[:200]}")
    
    # Test analytics
    data, err = api_get("/api/analytics/dashboard", headers)
    if err:
        log_result("HR: Analytics Dashboard", "FAIL", err, "MEDIUM")
    else:
        log_result("HR: Analytics Dashboard", "PASS", "Dashboard accessible")
    
    data, err = api_get("/api/analytics/funnel", headers)
    if err:
        log_result("HR: Analytics Funnel", "FAIL", err, "MEDIUM")
    else:
        log_result("HR: Analytics Funnel", "PASS", "Funnel data accessible")
    
    # Test hiring cycles
    data, err = api_get("/api/hiring-cycles", headers)
    if err:
        log_result("HR: Hiring Cycles", "FAIL", err, "MEDIUM")
    else:
        log_result("HR: Hiring Cycles", "PASS", "Hiring cycles accessible")

def test_candidate_endpoints(tokens):
    """Test candidate-accessible endpoints."""
    token = tokens.get("Candidate")
    if not token:
        log_result("Candidate Endpoints", "SKIP", "No candidate token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /me endpoint
    data, err = api_get("/api/candidates/me", headers)
    if err:
        log_result("Candidate: Get Me", "FAIL", err, "CRITICAL")
    else:
        log_result("Candidate: Get Me", "PASS", "Profile accessible")
    
    # Test assessment endpoint
    data, err = api_get("/api/assessment/active", headers)
    if err:
        log_result("Candidate: Active Assessment", "FAIL", err, "MEDIUM")
    else:
        log_result("Candidate: Active Assessment", "PASS", "Assessment info accessible")

def test_screening(tokens):
    """Test screening execution."""
    token = tokens.get("HR") or tokens.get("Super Admin") or tokens.get("Admin")
    if not token:
        log_result("Screening Test", "SKIP", "No authorized token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get pipeline stats before
    data, err = api_get("/api/screening/pipeline-stats", headers)
    if err:
        log_result("Screening: Pre-check", "FAIL", err, "HIGH")
        return
    
    # Try running screening
    data, err = api_post("/api/screening/run", {"filters": {}}, headers)
    if err:
        # May return 0 screened if no APPLIED candidates
        log_result("Screening: Run", "WARN" if "screened" not in str(data or "") else "PASS", 
                   f"Screening result: {str(data)[:200] if data else err}", "MEDIUM")
    else:
        result = data.get("data", data) if isinstance(data, dict) else data
        screened = result.get("screened", 0) if isinstance(result, dict) else 0
        passed = result.get("passed", 0) if isinstance(result, dict) else 0
        log_result("Screening: Run", "PASS", f"Screened {screened}, passed {passed}")

def test_interviewer_endpoints(tokens):
    """Test interviewer endpoints."""
    token = tokens.get("Interviewer")
    if not token:
        log_result("Interviewer Endpoints", "SKIP", "No interviewer token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try listing candidates (interviewer may have limited access)
    data, err = api_get("/api/candidates/", headers)
    if err:
        # 403 is expected if interviewers can't list all candidates
        if "403" in str(err):
            log_result("Interviewer: RBAC on Candidates", "PASS", "Correctly blocked from listing candidates (expected 403)")
        else:
            log_result("Interviewer: List Candidates", "FAIL", err, "HIGH")
    else:
        log_result("Interviewer: List Candidates", "PASS", "Can access candidates list")

def check_db_integrity():
    """Check database health and integrity."""
    import sqlite3
    db_path = "/mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db"
    if not os.path.exists(db_path):
        log_result("DB: Database File", "FAIL", f"DB not found at {db_path}", "CRITICAL")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Get table list
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cur.fetchall()]
        log_result("DB: Tables", "PASS", f"Found {len(tables)} tables: {', '.join(tables[:15])}")
        
        # Check each table for row count
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM \"{table}\"")
                count = cur.fetchone()[0]
                if count > 0:
                    log_result(f"DB: {table}", "PASS", f"{count} rows")
            except Exception as e:
                log_result(f"DB: {table}", "WARN", str(e)[:100], "LOW")
        
        conn.close()
        REPORT["systems"]["database"] = "HEALTHY"
    except Exception as e:
        log_result("DB: Integrity", "FAIL", str(e), "CRITICAL")
        REPORT["systems"]["database"] = "UNHEALTHY"

def check_auth_rbac():
    """Check that unauthenticated access is blocked for protected endpoints."""
    protected_endpoints = [
        "/api/candidates/",
        "/api/admin/users",
        "/api/analytics/dashboard",
        "/api/screening/run",
    ]
    
    blocked = 0
    for ep in protected_endpoints:
        if ep == "/api/screening/run":
            data, err = api_post(ep, {})
        else:
            data, err = api_get(ep)
        
        if err and ("401" in str(err) or "403" in str(err)):
            blocked += 1
        elif err:
            log_result(f"RBAC: {ep}", "WARN", f"Error but not auth: {err}", "LOW")
        else:
            log_result(f"RBAC: {ep}", "FAIL", f"Endpoint accessible without auth!", "CRITICAL")
    
    if blocked == len(protected_endpoints):
        log_result("RBAC: Auth Required", "PASS", f"All {blocked}/{len(protected_endpoints)} endpoints block unauthenticated access")
    else:
        log_result("RBAC: Auth Required", "WARN", f"{blocked}/{len(protected_endpoints)} endpoints blocked unauthenticated", "HIGH")

def save_report():
    """Save the run report."""
    run_dir = f"{BASE_DIR}/qa_runs"
    os.makedirs(run_dir, exist_ok=True)
    
    # Save current run
    path = f"{run_dir}/{RUN_ID}.json"
    with open(path, "w") as f:
        json.dump(REPORT, f, indent=2, default=str)
    
    # Clean old runs (keep last 10)
    runs = sorted([f for f in os.listdir(run_dir) if f.endswith(".json") and f[0].isdigit()])
    for old in runs[:-10]:
        os.remove(f"{run_dir}/{old}")
    
    return path

def main():
    print(f"=== Knowledge Factory QA Cron Run {RUN_ID} ===")
    print(f"Target: {BASE_URL}")
    print()
    
    # 1. Health check
    print("[1/6] Health Check...")
    if not test_health():
        print("  ❌ Backend is DOWN - aborting further tests")
        log_result("Full Test Suite", "FAIL", "Backend down - suite aborted", "CRITICAL")
        save_report()
        print(json.dumps(REPORT, indent=2, default=str))
        sys.exit(1)
    print("  ✅ Backend healthy")
    
    # 2. Database integrity
    print("[2/6] Database Integrity...")
    check_db_integrity()
    
    # 3. Test logins
    print("[3/6] Authentication Tests...")
    tokens, login_ok = test_logins()
    if not login_ok:
        print("  ⚠️  Some logins failed")
    
    # 4. RBAC tests
    print("[4/6] RBAC Tests...")
    check_auth_rbac()
    
    # 5. Feature tests
    print("[5/6] Feature Endpoint Tests...")
    test_admin_endpoints(tokens)
    test_hr_endpoints(tokens)
    test_candidate_endpoints(tokens)
    test_interviewer_endpoints(tokens)
    test_screening(tokens)
    
    # 6. Summary
    print("[6/6] Finalizing...")
    path = save_report()
    
    print()
    print(f"=== SUMMARY ===")
    print(f"  Passed:  {REPORT['summary']['passed']}")
    print(f"  Failed:  {REPORT['summary']['failed']}")
    print(f"  Warnings: {REPORT['summary']['warnings']}")
    print()
    
    if REPORT["failures"]:
        print("=== FAILURES ===")
        for f in REPORT["failures"]:
            print(f"  ❌ [{f['severity']}] {f['name']}: {f.get('detail', '')}")
    
    print()
    print(f"Report saved to: {path}")
    
    # Return the report as JSON for processing
    return REPORT

if __name__ == "__main__":
    report = main()
    # Output final JSON for downstream processing
    print("===REPORT_JSON===")
    print(json.dumps(report, indent=2, default=str))
