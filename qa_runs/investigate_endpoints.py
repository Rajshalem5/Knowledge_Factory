#!/usr/bin/env python3
"""Investigate API endpoints that failed."""
import urllib.request, urllib.error, json

BASE_URL = "http://localhost:8000"

def api_get(path, token=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
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

def api_post(path, body, token=None):
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

# Login first (manual API call, no need for direct import)
print("=== Login as admin ===")
status, data = api_post("/api/auth/login", {"email": "admin@knowledgefactory.io", "password": "admin123"})
token = data.get("access_token", "")
print(f"  Login: {status}, has token: {bool(token)}")
role = data.get("role", "?")
print(f"  Role: {role}")

if token:
    print("\n=== Check admin/logs ===")
    status, data = api_get("/api/admin/logs", token=token)
    print(f"  GET /api/admin/logs: {status} — {str(data)[:200]}")
    
    # Try alternative paths
    for path in ["/api/admin/audit-logs", "/api/audit/logs", "/api/admin/audit"]:
        status, data = api_get(path, token=token)
        print(f"  GET {path}: {status} — {str(data)[:100]}")
    
    print("\n=== Check interview feedback paths ===")
    # Login as alice
    status2, data2 = api_post("/api/auth/login", {"email": "alice@test.com", "password": "Candidate@123"})
    alice_token = data2.get("access_token", "")
    if alice_token:
        for path in ["/api/candidates/me/feedback", "/api/interviews/feedback"]:
            status, data = api_get(path, token=alice_token)
            print(f"  GET {path} (as alice): {status}")
        
        for path in ["/api/candidates/me/feedback", "/api/interviews/feedback"]:
            status, data = api_get(path, token=token)
            print(f"  GET {path} (as admin): {status}")
    
    print("\n=== Check selection endpoint methods ===")
    status, data = api_get("/api/selection/bulk-select", token=token)
    print(f"  GET /api/selection/bulk-select: {status}")
    for method in ["PATCH", "PUT"]:
        url = f"{BASE_URL}/api/selection/bulk-select"
        data_bytes = json.dumps({"candidate_ids": []}).encode()
        req = urllib.request.Request(url, data=data_bytes, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode()
                print(f"  {method} /api/selection/bulk-select: {resp.status} — {body[:100]}")
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            print(f"  {method} /api/selection/bulk-select: {e.code} — {body[:100]}")
    
    print("\n=== Check hiring cycles registration schema ===")
    import time
    ts = int(time.time())
    for body in [
        {"email": f"qa_schema_{ts}@test.com", "password": "QaPass@12345", "name": "QA User", "role": "candidate", "phone": "+911234567890", "college": "Test", "branch": "CSE", "cgpa": 8.5, "passed_out_year": 2026},
        {"email": f"qa_schema2_{ts}@test.com", "password": "QaPass@12345", "full_name": "QA User", "role": "candidate", "college": "Test", "branch": "CSE", "cgpa": 8.5, "passed_out_year": 2026},
    ]:
        status, data = api_post("/api/auth/register", body)
        print(f"  Register {body.get('email','?')}: {status} — {str(data)[:100]}")
