"""Verify candidate listing works correctly."""
import httpx

BASE = "http://localhost:8000"

# Login as admin
r = httpx.post(f"{BASE}/api/auth/login", json={"email": "admin@knowledgefactory.io", "password": "admin123"})
token = r.json()["access_token"]

# List without filters (no cycle_id)
r = httpx.get(f"{BASE}/api/candidates/", headers={"Authorization": f"Bearer {token}"})
print(f"GET /api/candidates/ (no filters): {r.status_code}")
data = r.json()
candidates = data.get("data", [])
pagination = data.get("pagination", {})
print(f"  Candidates returned: {len(candidates)}")
print(f"  Pagination: total={pagination.get('total', '?')}, page={pagination.get('page', '?')}")
assert len(candidates) > 0, "Expected candidates in response!"

# List as HR
r = httpx.post(f"{BASE}/api/auth/login", json={"email": "hr@knowledgefactory.io", "password": "Hr@12345"})
token_hr = r.json()["access_token"]
r = httpx.get(f"{BASE}/api/candidates/", headers={"Authorization": f"Bearer {token_hr}"})
print(f"\nGET /api/candidates/ (HR): {r.status_code}")
data = r.json()
print(f"  Candidates returned: {len(data.get('data', []))}")
assert len(data.get("data", [])) > 0, "Expected candidates for HR!"

print("\n✅ Candidate listing works for both admin and HR!")
