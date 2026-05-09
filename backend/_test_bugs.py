"""Test status filter and duplicate registration."""
import httpx, json, sys

BASE = "http://127.0.0.1:8001"

# Login as admin
r = httpx.post(f"{BASE}/api/auth/login", json={
    "email": "admin@knowledgefactory.io", "password": "admin123"
})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test 1: Status filter with display_status value
print("=== Test 1: Status filter with 'applied' ===")
r = httpx.get(f"{BASE}/api/candidates", params={"status": "applied"}, headers=headers)
print(f"  Status: {r.status_code}, Body: {r.text[:200]}")

# Test 2: Status filter with raw backend value
print("=== Test 2: Status filter with 'APPLIED' ===")
r = httpx.get(f"{BASE}/api/candidates", params={"status": "APPLIED"}, headers=headers)
print(f"  Status: {r.status_code}, Body: {r.text[:200]}")

# Test 3: Duplicate registration
print("=== Test 3: Register duplicate email ===")
r = httpx.post(f"{BASE}/api/auth/register", data={
    "name": "Dup", "email": "pipeline-test@example.com",
    "password": "Test@123", "college": "T", "branch": "CSE",
    "cgpa": 8.0, "passed_out_year": 2026, "language_choice": "python"
})
print(f"  Status: {r.status_code}, Body: {r.text[:200]}")
