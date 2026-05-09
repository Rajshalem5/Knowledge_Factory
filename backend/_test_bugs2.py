"""Test status filter and duplicate registration."""
import httpx, json, sys

BASE = "http://127.0.0.1:8001"

# Login as admin
r = httpx.post(f"{BASE}/api/auth/login", json={
    "email": "admin@knowledgefactory.io", "password": "admin123"
})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test 1: Status filter with display_status value (use trailing slash)
print("=== Test 1: Status filter with 'applied' ===")
r = httpx.get(f"{BASE}/api/candidates/", params={"status": "applied"}, headers=headers)
print(f"  Status: {r.status_code}, Body: {r.text[:300]}")

# Test 2: Status filter with raw backend value
print("=== Test 2: Status filter with 'APPLIED' ===")
r = httpx.get(f"{BASE}/api/candidates/", params={"status": "APPLIED"}, headers=headers)
print(f"  Status: {r.status_code}, Body: {r.text[:300]}")

# Test 3: Check pipeline-stats with search filter (not supported)
print("=== Test 3: pipeline-stats ===")
r = httpx.get(f"{BASE}/api/screening/pipeline-stats", headers=headers)
print(f"  Status: {r.status_code}, Body: {r.text[:300]}")

# Test 4: Check pipeline-stats with passed_out_year filter
print("=== Test 4: pipeline-stats with filters ===")
r = httpx.get(f"{BASE}/api/screening/pipeline-stats", params={"branch": "CSE"}, headers=headers)
print(f"  Status: {r.status_code}, Body: {r.text[:300]}")
