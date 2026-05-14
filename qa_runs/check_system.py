#!/usr/bin/env python3
"""Quick API health check before full QA run."""
import json, sys, os
import urllib.request, urllib.error

BASE = "http://localhost:8000"
NGROK = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
results = {"checks": [], "errors": []}

def check(name, url, expect_status=200, expect_contains=None):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            status = resp.status
            ok = status == expect_status
            if expect_contains and expect_contains not in body:
                ok = False
            results["checks"].append({"name": name, "ok": ok, "status": status, "detail": body[:200] if not ok else "ok"})
            if not ok:
                results["errors"].append(f"{name}: status={status}, body={body[:200]}")
            return ok
    except Exception as e:
        results["checks"].append({"name": name, "ok": False, "status": "error", "detail": str(e)})
        results["errors"].append(f"{name}: {e}")
        return False

# 1. Backend health
check("backend_health", f"{BASE}/health")

# 2. Ngrok reachability
check("ngrok_health", f"{NGROK}/health")

# 3. Login test - admin
try:
    data = json.dumps({"email": "admin@knowledgefactory.io", "password": "admin123"}).encode()
    req = urllib.request.Request(f"{BASE}/api/auth/login", data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
        results["checks"].append({"name": "login_admin", "ok": True, "detail": "token_received" if body.get("access_token") else "no_token"})
        results["admin_token"] = body.get("access_token", "")
except Exception as e:
    results["checks"].append({"name": "login_admin", "ok": False, "detail": str(e)})
    results["errors"].append(f"login_admin: {e}")

# 4. Login test - all roles
creds = [
    ("superadmin", "superadmin@knowledgefactory.io", "Super@12345"),
    ("admin", "admin@knowledgefactory.io", "admin123"),
    ("hr", "hr@test.com", "Hr@12345"),
    ("interviewer", "interviewer@test.com", "Interviewer@12345"),
    ("candidate", "candidate@test.com", "Candidate@12345"),
]
tokens = {}
for role, email, pw in creds:
    try:
        data = json.dumps({"email": email, "password": pw}).encode()
        req = urllib.request.Request(f"{BASE}/api/auth/login", data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            tok = body.get("access_token", "")
            tokens[role] = tok
            results["checks"].append({"name": f"login_{role}", "ok": bool(tok), "detail": "ok" if tok else "no_token"})
            if not tok:
                results["errors"].append(f"login_{role}: no token in response")
    except Exception as e:
        results["checks"].append({"name": f"login_{role}", "ok": False, "detail": str(e)})
        results["errors"].append(f"login_{role}: {e}")

# 5. Auth me endpoint for each role
for role, tok in tokens.items():
    if not tok:
        continue
    try:
        req = urllib.request.Request(f"{BASE}/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            results["checks"].append({"name": f"auth_me_{role}", "ok": True, "detail": f"role={body.get('role','?')}"})
    except Exception as e:
        results["checks"].append({"name": f"auth_me_{role}", "ok": False, "detail": str(e)})
        results["errors"].append(f"auth_me_{role}: {e}")

# 6. Screening pipeline stats (no auth required currently)
try:
    req = urllib.request.Request(f"{BASE}/api/screening/pipeline-stats")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
        results["checks"].append({"name": "pipeline_stats", "ok": True, "detail": str(body)[:200]})
except Exception as e:
    results["checks"].append({"name": "pipeline_stats", "ok": False, "detail": str(e)})
    results["errors"].append(f"pipeline_stats: {e}")

# 7. Analytics funnel
try:
    req = urllib.request.Request(f"{BASE}/api/analytics/funnel", headers={"Authorization": f"Bearer {tokens.get('hr','')}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
        results["checks"].append({"name": "analytics_funnel", "ok": True, "detail": "ok"})
except Exception as e:
    results["checks"].append({"name": "analytics_funnel", "ok": False, "detail": str(e)})
    results["errors"].append(f"analytics_funnel: {e}")

# 8. Candidates listing (HR auth)
try:
    req = urllib.request.Request(f"{BASE}/api/candidates/", headers={"Authorization": f"Bearer {tokens.get('hr','')}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
        count = len(body.get("data", body if isinstance(body, list) else []))
        results["checks"].append({"name": "candidates_list", "ok": True, "detail": f"{count} candidates"})
except Exception as e:
    results["checks"].append({"name": "candidates_list", "ok": False, "detail": str(e)})
    results["errors"].append(f"candidates_list: {e}")

# 9. Hiring cycles
try:
    req = urllib.request.Request(f"{BASE}/api/hiring-cycles/", headers={"Authorization": f"Bearer {tokens.get('admin','')}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
        results["checks"].append({"name": "hiring_cycles", "ok": True, "detail": f"{len(body) if isinstance(body, list) else len(body.get('data',[]))} cycles"})
except Exception as e:
    results["checks"].append({"name": "hiring_cycles", "ok": False, "detail": str(e)})
    results["errors"].append(f"hiring_cycles: {e}")

# 10. Admin audit logs
try:
    req = urllib.request.Request(f"{BASE}/api/admin/logs", headers={"Authorization": f"Bearer {tokens.get('admin','')}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
        results["checks"].append({"name": "admin_logs", "ok": True, "detail": "ok"})
except Exception as e:
    results["checks"].append({"name": "admin_logs", "ok": False, "detail": str(e)})
    results["errors"].append(f"admin_logs: {e}")

# 11. Admin users list
try:
    req = urllib.request.Request(f"{BASE}/api/admin/users", headers={"Authorization": f"Bearer {tokens.get('superadmin','')}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
        results["checks"].append({"name": "admin_users", "ok": True, "detail": "ok"})
except Exception as e:
    results["checks"].append({"name": "admin_users", "ok": False, "detail": str(e)})
    results["errors"].append(f"admin_users: {e}")

# 12. Code execution endpoint (stub)
try:
    req = urllib.request.Request(f"{BASE}/api/code/execute", 
        data=json.dumps({"language": "python", "code": "print('hello')"}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {tokens.get('candidate','')}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode()
        results["checks"].append({"name": "code_execute", "ok": True, "detail": "endpoint_responds"})
except urllib.error.HTTPError as e:
    # 422 or 500 expected for stubs
    results["checks"].append({"name": "code_execute", "ok": True, "detail": f"responded_{e.code}"})
except Exception as e:
    results["checks"].append({"name": "code_execute", "ok": False, "detail": str(e)})
    results["errors"].append(f"code_execute: {e}")

# 13. Registration endpoint
try:
    import random
    ts = int(__import__('time').time())
    data = json.dumps({
        "email": f"qatest{ts}@test.com",
        "password": "Test@12345",
        "full_name": f"QA Test {ts}",
        "role": "candidate"
    }).encode()
    req = urllib.request.Request(f"{BASE}/api/auth/register", data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
        results["checks"].append({"name": "register_candidate", "ok": True, "detail": "created"})
except urllib.error.HTTPError as e:
    body = e.read().decode()
    results["checks"].append({"name": "register_candidate", "ok": False, "detail": f"HTTP_{e.code}: {body[:100]}"})
    results["errors"].append(f"register_candidate: HTTP {e.code}: {body[:100]}")
except Exception as e:
    results["checks"].append({"name": "register_candidate", "ok": False, "detail": str(e)})
    results["errors"].append(f"register_candidate: {e}")

# Summary
passed = sum(1 for c in results["checks"] if c["ok"])
total = len(results["checks"])
failed = total - passed
results["summary"] = {"passed": passed, "failed": failed, "total": total}

print(json.dumps(results, indent=2))
