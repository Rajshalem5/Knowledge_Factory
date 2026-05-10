#!/usr/bin/env python3
"""Full end-to-end pipeline test - connects to running server."""
import httpx
import uuid
import time
import sys

BASE = "http://127.0.0.1:8002"
UNIQUE = str(int(time.time()))
EMAIL = f"e2e-{UNIQUE}@test.com"

def log(step, status, detail=""):
    status_str = str(status)
    mark = "✓" if status_str.startswith("2") or status_str.startswith("3") else "✗"
    print(f"{mark} {step}: HTTP {status} {detail}")

# Step 1: Register a new candidate
r = httpx.post(f"{BASE}/api/auth/register", json={
    "name": f"E2E Test {UNIQUE}",
    "email": EMAIL,
    "password": "Candidate@123",
    "college": "Test University",
    "branch": "CSE",
    "cgpa": 8.5,
    "passed_out_year": 2026,
    "language_choice": "python",
})
log("Register", r.status_code)
if r.status_code != 201:
    print(f"  ERROR: {r.text[:300]}")
    sys.exit(1)
candidate_token = r.json()["access_token"]
candidate_headers = {"Authorization": f"Bearer {candidate_token}"}

# Step 2: Get my profile
r = httpx.get(f"{BASE}/api/candidates/me", headers=candidate_headers)
log("GET /candidates/me", r.status_code)
assert r.status_code == 200, f"FAIL: {r.text}"
print(f"  Status: {r.json()['status']}, display: {r.json()['display_status']}")
assert r.json()["display_status"] == "applied"
candidate_id = r.json()["id"]

# Step 3: Login as admin
r = httpx.post(f"{BASE}/api/auth/login", json={
    "email": "ops@test.com",
    "password": "Ops@12345",
})
log("Admin login", r.status_code, r.text[:200] if r.status_code != 200 else "")
if r.status_code != 200:
    print("  Can't login as staff - need to find working credentials")
    print(f"  Response: {r.text[:200]}")
    sys.exit(1)

admin_token = r.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# Step 4: Run screening
r = httpx.post(f"{BASE}/api/screening/run", headers=admin_headers)
log("Run screening", r.status_code)
if r.status_code != 200:
    print(f"  ERROR: {r.text[:500]}")
    sys.exit(1)
screening_result = r.json()
print(f"  Result: screened={screening_result['screened']}, passed={screening_result['passed']}, rejected={screening_result['rejected']}")

# Step 5: Check candidate status after screening
r = httpx.get(f"{BASE}/api/candidates/me", headers=candidate_headers)
log("Status after screening", r.status_code)
print(f"  Status: {r.json()['status']}, display: {r.json()['display_status']}")
assert r.json()["status"] == "ROUND1_PASSED", f"Expected ROUND1_PASSED, got {r.json()['status']}"

# Step 6: Start assessment ROUND_2
r = httpx.post(f"{BASE}/api/assessment/start", headers=candidate_headers, json={"round": "ROUND_2"})
log("Start assessment", r.status_code)
if r.status_code != 200:
    print(f"  ERROR: {r.text[:500]}")
    sys.exit(1)
assessment = r.json()
print(f"  Assessment: id={assessment['id'][:8]}..., round={assessment['round']}, status={assessment['status']}")
assert assessment["status"] == "IN_PROGRESS"

# Step 7: Check candidate status
r = httpx.get(f"{BASE}/api/candidates/me", headers=candidate_headers)
log("Status after start", r.status_code)
print(f"  Status: {r.json()['status']}")
assert r.json()["status"] == "ROUND2_IN_PROGRESS"

# Step 8: Submit section
r = httpx.post(f"{BASE}/api/assessment/submit-section", headers=candidate_headers, json={
    "assessment_id": assessment["id"],
    "section": "CODING",
    "content": {"code": "print('hello')", "problemId": "r2_p1"},
    "time_spent_seconds": 120,
})
log("Submit section", r.status_code)
if r.status_code != 200:
    print(f"  ERROR: {r.text[:500]}")
    sys.exit(1)
print(f"  Result: {r.json()}")

# Step 9: Complete assessment
r = httpx.post(f"{BASE}/api/assessment/{assessment['id']}/complete", headers=candidate_headers)
log("Complete assessment", r.status_code)
if r.status_code != 200:
    print(f"  ERROR: {r.text[:500]}")
    sys.exit(1)
print(f"  Assessment status: {r.json()['status']}")
assert r.json()["status"] == "COMPLETED"

# Step 10: Check candidate status after completion
r = httpx.get(f"{BASE}/api/candidates/me", headers=candidate_headers)
log("Status after complete", r.status_code)
print(f"  Status: {r.json()['status']}")
assert r.json()["status"] == "ROUND2_PASSED", f"Expected ROUND2_PASSED, got {r.json()['status']}"

# Step 11: Start ROUND_3
r = httpx.post(f"{BASE}/api/assessment/start", headers=candidate_headers, json={"round": "ROUND_3"})
log("Start ROUND_3", r.status_code)
if r.status_code != 200:
    print(f"  ERROR: {r.text[:500]}")
    sys.exit(1)
print(f"  Assessment: id={r.json()['id'][:8]}..., round={r.json()['round']}, status={r.json()['status']}")

# Step 12: Final status check
r = httpx.get(f"{BASE}/api/candidates/me", headers=candidate_headers)
log("Final status", r.status_code)
print(f"  Status: {r.json()['status']}")
assert r.json()["status"] == "ROUND3_IN_PROGRESS", f"Expected ROUND3_IN_PROGRESS, got {r.json()['status']}"

print("\n" + "="*60)
print("✓ FULL PIPELINE E2E TEST PASSED!")
print("="*60)
sys.exit(0)
