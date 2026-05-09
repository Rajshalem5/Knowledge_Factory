"""
Clean E2E pipeline test with unique email per run.
Verifies: Screening -> Assessment (ROUND_2) -> Complete -> Assessment (ROUND_3)
"""
import httpx
import json
import time

BASE = "http://127.0.0.1:8001"
UNIQUE = str(int(time.time()))
EMAIL = f"pipeline-{UNIQUE}@test.com"

client = httpx.Client(timeout=10)

def log(label, resp):
    status = resp.status_code
    try:
        body = resp.json()
    except:
        body = resp.text[:200]
    detail = json.dumps(body, indent=2) if isinstance(body, dict) else str(body)[:200]
    return resp

print("=" * 60)
print(f"CLEAN E2E PIPELINE TEST ({UNIQUE})")
print("=" * 60)

# [1] Login as admin
r = log("login", client.post(f"{BASE}/api/auth/login", json={
    "email": "admin@knowledgefactory.io", "password": "admin123"
}))
assert r.status_code == 200, f"Admin login failed: {r.text}"
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# [2] Register candidate (unique email)
r = log("register", client.post(f"{BASE}/api/auth/register", data={
    "name": f"Pipeline Test {UNIQUE}",
    "email": EMAIL,
    "password": "Test@123",
    "college": "Test University",
    "branch": "CSE",
    "cgpa": "8.5",
    "passed_out_year": "2026",
    "language_choice": "python"
}))
assert r.status_code == 201, f"Register failed: {r.text}"
user = r.json()["user"]
cid = user["id"]
candidate_token = r.json()["access_token"]
candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
print(f"  Candidate created: {cid} / {EMAIL}")

# [3] Verify APPLIED status
r = client.get(f"{BASE}/api/candidates/{cid}", headers=headers)
assert r.status_code == 200, f"GET candidate failed: {r.text}"
assert r.json()["status"] == "APPLIED", f"Expected APPLIED, got {r.json()['status']}"
print("  ✓ Status: APPLIED")

# [4] Run screening
r = client.post(f"{BASE}/api/screening/run", headers=headers)
assert r.status_code == 200, f"Screening failed: {r.text}"
s = r.json()
print(f"  ✓ Screening: {s['screened']} screened, {s['passed']} passed")

# [5] Verify ROUND1_PASSED  
r = client.get(f"{BASE}/api/candidates/{cid}", headers=headers)
assert r.status_code == 200
assert r.json()["status"] == "ROUND1_PASSED", f"Expected ROUND1_PASSED, got {r.json()['status']}"
print("  ✓ Status: ROUND1_PASSED")

# [6] Login as candidate
r = client.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": "Test@123"})
assert r.status_code == 200, f"Candidate login failed: {r.text}"
candidate_token = r.json()["access_token"]
candidate_headers = {"Authorization": f"Bearer {candidate_token}"}

# [7] Get candidate profile (me)
r = client.get(f"{BASE}/api/candidates/me", headers=candidate_headers)
assert r.status_code == 200
profile = r.json()
assert profile["status"] == "ROUND1_PASSED", f"Expected ROUND1_PASSED, got {profile['status']}"
assert profile["display_status"] == "eligible"
print(f"  ✓ Profile: status={profile['status']}, display={profile['display_status']}")

# [8] Start ROUND_2 assessment
r = client.post(f"{BASE}/api/assessment/start", json={"round": "ROUND_2"}, headers=candidate_headers)
assert r.status_code == 200, f"Start R2 failed: {r.text}"
assessment = r.json()
assert assessment["status"] == "IN_PROGRESS"
a_id = assessment["id"]
print(f"  ✓ R2 assessment created: {a_id}")

# [9] Verify ROUND2_IN_PROGRESS
r = client.get(f"{BASE}/api/candidates/me", headers=candidate_headers)
cand = r.json()
assert cand["status"] == "ROUND2_IN_PROGRESS", f"Expected ROUND2_IN_PROGRESS, got {cand['status']}"
print("  ✓ Status: ROUND2_IN_PROGRESS")

# [10] Get active assessments
r = client.get(f"{BASE}/api/assessment/active", headers=candidate_headers)
actives = r.json()
assert len(actives) >= 1
print(f"  ✓ Active assessments: {len(actives)}")

# [11] Complete assessment
r = client.post(f"{BASE}/api/assessment/{a_id}/complete", headers=candidate_headers)
assert r.status_code == 200, f"Complete failed: {r.text}"
assert r.json()["status"] == "COMPLETED"
print("  ✓ Assessment completed")

# [12] Verify ROUND2_PASSED
r = client.get(f"{BASE}/api/candidates/me", headers=candidate_headers)
cand = r.json()
assert cand["status"] == "ROUND2_PASSED", f"Expected ROUND2_PASSED, got {cand['status']}"
print("  ✓ Status: ROUND2_PASSED")

# [13] Start ROUND_3 assessment
r = client.post(f"{BASE}/api/assessment/start", json={"round": "ROUND_3"}, headers=candidate_headers)
assert r.status_code == 200, f"Start R3 failed: {r.text}"
assert r.json()["status"] == "IN_PROGRESS"
print("  ✓ R3 assessment started")

# [14] Verify ROUND3_IN_PROGRESS
r = client.get(f"{BASE}/api/candidates/me", headers=candidate_headers)
cand = r.json()
assert cand["status"] == "ROUND3_IN_PROGRESS", f"Expected ROUND3_IN_PROGRESS, got {cand['status']}"
print("  ✓ Status: ROUND3_IN_PROGRESS")

print("\n" + "=" * 60)
print("ALL PIPELINE STEPS PASSED!")
print("=" * 60)
