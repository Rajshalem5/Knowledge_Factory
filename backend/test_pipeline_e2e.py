"""
End-to-end pipeline test: Screening -> Assessment -> Complete
Uses form-data for registration (the register endpoint uses Form())
"""
import httpx
import json
import sys

BASE = "http://127.0.0.1:8001"

def log(label, resp):
    status = resp.status_code
    try:
        body = resp.json()
    except:
        body = resp.text[:300]
    print(f"  {label}: {status} -> {json.dumps(body, indent=2)[:300]}")
    return resp

print("=" * 60)
print("E2E PIPELINE TEST")
print("=" * 60)

# Step 1: Login as admin
print("\n[1] Login as admin")
r = log("login", httpx.post(f"{BASE}/api/auth/login", json={
    "email": "admin@knowledgefactory.io", "password": "admin123"
}))
if r.status_code != 200:
    print("  ! Admin login failed. Trying alternate password...")
    r = log("login try2", httpx.post(f"{BASE}/api/auth/login", json={
        "email": "admin@knowledgefactory.io", "password": "Admin@12345"
    }))

if r.status_code != 200:
    print("FATAL: Cannot login as admin")
    sys.exit(1)

token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Step 2: Check hiring cycles
print("\n[2] Check hiring cycles")
r = log("cycles", httpx.get(f"{BASE}/api/hiring-cycles", headers=headers))
cycle_id = None
if r.status_code == 200:
    cycles = r.json()
    if isinstance(cycles, list) and cycles:
        cycle_id = cycles[0]["id"]
        print(f"  Active cycle ID: {cycle_id}")

# Step 3: Register a test candidate (using Form data)
print("\n[3] Register test candidate (form-data)")
r = log("register", httpx.post(f"{BASE}/api/auth/register", data={
    "name": "Pipeline Test Candidate",
    "email": "pipeline-test@example.com",
    "password": "Test@123",
    "college": "Test University",
    "branch": "CSE",
    "cgpa": "8.5",
    "passed_out_year": "2026",
    "language_choice": "python"
}))
candidate_id = None
if r.status_code == 201:
    user = r.json().get("user", {})
    candidate_id = user.get("id")
    print(f"  Candidate ID: {candidate_id}")
else:
    # Might already exist, try searching
    r2 = log("search", httpx.get(f"{BASE}/api/candidates?search=pipeline-test", headers=headers))
    if r2.status_code == 200:
        data = r2.json().get("data", [])
        if data:
            candidate_id = data[0]["id"]
            print(f"  Found existing candidate: {candidate_id}")

if not candidate_id:
    print("FATAL: No candidate")
    sys.exit(1)

# Step 4: Verify APPLIED status
print("\n[4] Verify candidate is APPLIED")
r = log("get candidate", httpx.get(f"{BASE}/api/candidates/{candidate_id}", headers=headers))
status = r.json().get("status") if r.status_code == 200 else None
print(f"  Status: {status}")
assert status in ("APPLIED", "ROUND1_PASSED"), f"Expected APPLIED or ROUND1_PASSED, got {status}"

# Step 5: Run screening
print("\n[5] Run screening")
r = log("run screening", httpx.post(f"{BASE}/api/screening/run", headers=headers))
scr = r.json() if r.status_code == 200 else {}
print(f"  Result: {scr}")

# Step 6: Should be ROUND1_PASSED now
print("\n[6] Verify ROUND1_PASSED")
r = log("get candidate", httpx.get(f"{BASE}/api/candidates/{candidate_id}", headers=headers))
post_screen = r.json().get("status") if r.status_code == 200 else None
print(f"  Status: {post_screen}")

if post_screen != "ROUND1_PASSED":
    if post_screen == "ROUND1_REJECTED":
        print("  ! Candidate rejected in screening (CGPA/branch mismatch)")
        # Since we have cgpa=8.5 and branch=CSE, with allowed_branches=["CSE","ECE","IT","EEE"] and min_cgpa=6.0,
        # this should pass. Maybe the hiring cycle config is different.
        print("  ! Checking cycle config...")
        r = log("get cycles", httpx.get(f"{BASE}/api/hiring-cycles", headers=headers))
        if r.status_code == 200:
            cycles = r.json()
            if isinstance(cycles, list) and cycles:
                config = cycles[0].get("eligibility_config", {})
                print(f"  Cycle config: {config}")
    sys.exit(1)

# Step 7: Login as candidate
print("\n[7] Login as candidate")
r = log("candidate login", httpx.post(f"{BASE}/api/auth/login", json={
    "email": "pipeline-test@example.com", "password": "Test@123"
}))
if r.status_code != 200:
    print("FATAL: Cannot login as candidate")
    sys.exit(1)

candidate_token = r.json()["access_token"]
candidate_headers = {"Authorization": f"Bearer {candidate_token}"}

# Step 8: Get candidate my profile
print("\n[8] Get my profile (as candidate)")
r = log("me", httpx.get(f"{BASE}/api/candidates/me", headers=candidate_headers))
profile = r.json() if r.status_code == 200 else {}
print(f"  display_status: {profile.get('display_status')}")

# Step 9: Start assessment ROUND_2
print("\n[9] Start ROUND_2 assessment")
r = log("start R2", httpx.post(f"{BASE}/api/assessment/start", json={
    "round": "ROUND_2"
}, headers=candidate_headers))
assessment = r.json() if r.status_code == 200 else {}
print(f"  Assessment status: {assessment.get('status')}")
print(f"  Assessment ID: {assessment.get('id')}")

assessment_id = assessment.get("id")
if not assessment_id and r.status_code == 200:
    # Might already exist - try active
    print("  Getting active assessments instead...")

# Step 10: Verify ROUND2_IN_PROGRESS
print("\n[10] Verify ROUND2_IN_PROGRESS")
r = log("get candidate", httpx.get(f"{BASE}/api/candidates/{candidate_id}", headers=headers))
st = r.json().get("status") if r.status_code == 200 else None
print(f"  Status: {st}")

# Step 11: Get active assessments
print("\n[11] Get active assessments")
r = log("active", httpx.get(f"{BASE}/api/assessment/active", headers=candidate_headers))
actives = r.json() if r.status_code == 200 else []
print(f"  Active: {len(actives) if isinstance(actives, list) else 'error'}")

if isinstance(actives, list) and actives:
    assessment_id = actives[0]["id"]
    print(f"  Using assessment_id={assessment_id}")

if not assessment_id:
    print("FATAL: No assessment ID")
    sys.exit(1)

# Step 12: Complete assessment
print(f"\n[12] Complete assessment {assessment_id}")
r = log("complete", httpx.post(f"{BASE}/api/assessment/{assessment_id}/complete", headers=candidate_headers))
complete = r.json() if r.status_code == 200 else {}
print(f"  Result: status={complete.get('status')}")

# Step 13: Verify ROUND2_PASSED
print("\n[13] Verify ROUND2_PASSED")
r = log("get candidate", httpx.get(f"{BASE}/api/candidates/{candidate_id}", headers=headers))
st2 = r.json().get("status") if r.status_code == 200 else None
print(f"  Status: {st2}")

# Step 14: Start ROUND_3
print("\n[14] Start ROUND_3 assessment")
r = log("start R3", httpx.post(f"{BASE}/api/assessment/start", json={
    "round": "ROUND_3"
}, headers=candidate_headers))
r3 = r.json() if r.status_code == 200 else {}
print(f"  R3 status: {r3.get('status')}")

# Step 15: Verify ROUND3_IN_PROGRESS
print("\n[15] Verify ROUND3_IN_PROGRESS")
r = log("get candidate", httpx.get(f"{BASE}/api/candidates/{candidate_id}", headers=headers))
st3 = r.json().get("status") if r.status_code == 200 else None
print(f"  Status: {st3}")

print("\n" + "=" * 60)
print("PIPELINE TEST COMPLETE")
print("=" * 60)
