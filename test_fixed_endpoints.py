#!/usr/bin/env python3
"""Quick verify audit logs + fixed endpoints"""
import requests, json

BASE = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"

# Login super admin
r = requests.post(f"{BASE}/api/auth/login", json={"email": "superadmin@knowledgefactory.io", "password": "Super@12345"})
token = r.json().get("access_token")
print(f"SA login: {r.status_code}")

# Test audit logs
r = requests.get(f"{BASE}/api/audit/logs", headers={"Authorization": f"Bearer {token}"})
print(f"\nAudit logs: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    logs = data.get("data", [])
    print(f"  Count: {len(logs)} logs")
    if logs:
        print(f"  Sample: {json.dumps(logs[0], default=str)[:200]}")
    print(f"  Pagination: {data.get('pagination')}")
else:
    print(f"  FAILED: {r.text[:200]}")

# Test interview feedback with admin token (correct path)
r2 = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@knowledgefactory.io", "password": "admin123"})
admin_token = r2.json().get("access_token")

# Get candidates
r = requests.get(f"{BASE}/api/candidates/", headers={"Authorization": f"Bearer {admin_token}"})
if r.status_code == 200:
    data = r.json()
    candidates = data.get("data") or data.get("candidates") or []
    print(f"\nCandidates: {len(candidates)}")
    if candidates:
        cid = candidates[0].get("id")
        print(f"First candidate ID: {cid}")
        # Test correct interview feedback path
        r = requests.get(f"{BASE}/api/candidates/{cid}/feedback", headers={"Authorization": f"Bearer {admin_token}"})
        print(f"Interview feedback (correct path): {r.status_code}")
        if r.status_code != 200:
            print(f"  Response: {r.text[:200]}")

# Test selection POST (correct path)
print(f"\nSelection bulk POST test:")
r = requests.post(f"{BASE}/api/selection/candidates/bulk-select", json={"candidate_ids": []}, headers={"Authorization": f"Bearer {admin_token}"})
print(f"  Bulk select: {r.status_code} - {r.text[:100]}")

print("\nDone!")
