#!/usr/bin/env python3
"""Test core API endpoints."""
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000"

def req(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.fp else str(e)
    except Exception as e:
        return 0, str(e)

# 1. Login
print("=== POST /api/auth/login ===")
status, data = req("POST", "/api/auth/login", {"email": "admin@knowledgefactory.io", "password": "admin123"})
print(f"Status: {status}")
if status == 200:
    token = data.get("access_token", "")
    role = data.get("user", {}).get("role", "???")
    print(f"Token: {token[:30]}... | Role: {role}")
    
    # 2. Candidates
    print("\n=== GET /api/candidates/ ===")
    status2, data2 = req("GET", "/api/candidates/", token=token)
    print(f"Status: {status2}")
    if status2 == 200:
        if isinstance(data2, list):
            print(f"Candidates: {len(data2)}")
        elif isinstance(data2, dict):
            print(f"Candidates keys: {list(data2.keys())}")
            for k, v in data2.items():
                if isinstance(v, list):
                    print(f"  {k}: {len(v)} items")
                else:
                    print(f"  {k}: {v}")
    
    # 3. Screening pipeline stats
    print("\n=== GET /api/screening/pipeline-stats ===")
    status3, data3 = req("GET", "/api/screening/pipeline-stats", token=token)
    print(f"Status: {status3}")
    if status3 == 200:
        print(json.dumps(data3, indent=2)[:600])
    
    # 4. Analytics dashboard
    print("\n=== GET /api/analytics/dashboard ===")
    status4, data4 = req("GET", "/api/analytics/dashboard", token=token)
    print(f"Status: {status4}")
    if status4 == 200:
        print(json.dumps(data4, indent=2)[:600])
    else:
        print(f"Error: {data4}")
    
    # 5. Assessment start
    print("\n=== POST /api/assessment/start ===")
    status5, data5 = req("POST", "/api/assessment/start", {"candidate_id": 1}, token=token)
    print(f"Status: {status5}")
    print(json.dumps(data5, indent=2)[:500] if isinstance(data5, dict) else data5[:500])
else:
    print(f"Login failed: {data}")
