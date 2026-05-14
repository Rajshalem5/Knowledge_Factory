#!/usr/bin/env python3
"""More investigation of select endpoints and feedback paths."""
import urllib.request, urllib.error, json

BASE_URL = "http://localhost:8000"

def api_call(method, path, body=None, token=None):
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

# Login
status, data = api_call("POST", "/api/auth/login", {"email": "admin@knowledgefactory.io", "password": "admin123"})
token = data.get("access_token", "")
print(f"Admin login: {status}, token={'yes' if token else 'no'}")

status, data = api_call("POST", "/api/auth/login", {"email": "alice@test.com", "password": "Candidate@123"})
alice_token = data.get("access_token", "")
print(f"Alice login: {status}, token={'yes' if alice_token else 'no'}")

if token:
    print("\n=== Selection endpoints ===")
    paths_methods = [
        ("GET", "/api/selection/"),
        ("POST", "/api/selection/"),
        ("GET", "/api/selection/select"),
        ("POST", "/api/selection/select"),
        ("PATCH", "/api/selection/select"),
        ("GET", "/api/selection/bulk-select"),
        ("POST", "/api/selection/bulk-select"),
        ("PATCH", "/api/selection/bulk-select"),
    ]
    for method, path in paths_methods:
        body = {"candidate_ids": []} if method in ("POST", "PATCH") else None
        status, data = api_call(method, path, body=body, token=token)
        print(f"  {method} {path}: {status}")

    print("\n=== Feedback endpoints ===")
    paths = [
        "/api/interviews/feedback",
        "/api/interviews/feedback/",
        "/api/candidates/",
    ]
    for path in paths:
        status, data = api_call("GET", path, token=token)
        print(f"  GET {path}: {status}")

    # Get a specific candidate ID
    status, data = api_call("GET", "/api/candidates/", token=token)
    if status == 200:
        candidates = data
        if isinstance(data, dict):
            for k in ("data", "candidates", "items", "results"):
                if k in data:
                    candidates = data[k]
                    break
        if candidates:
            cid = candidates[0].get("id", "?")
            print(f"\n=== Candidate feedback path test (id={cid}) ===")
            for path in [f"/api/candidates/{cid}/feedback", f"/api/interviews/feedback?candidate_id={cid}"]:
                status, data = api_call("GET", path, token=token)
                print(f"  GET {path}: {status} — {str(data)[:100]}")
                
                status, data = api_call("POST", path, body={"rating": 4, "feedback": "Good", "recommendation": "SELECT"}, token=token)
                print(f"  POST {path}: {status} — {str(data)[:100]}")

print("\n=== Registration schema (correct form) ===")
import time
ts = int(time.time())
for body in [
    {"email": f"qa_regtest_{ts}@test.com", "password": "QaPass@12345", "name": "QA User", "role": "candidate"},
    {"email": f"qa_regtest2_{ts}@test.com", "password": "QaPass@12345", "name": "QA User", "role": "candidate", "college": "Test", "branch": "CSE", "cgpa": 8.5, "passed_out_year": 2026},
]:
    status, data = api_call("POST", "/api/auth/register", body)
    print(f"  Register {body.get('email','?')}: {status}")
