"""Live E2E test of the screening-to-assessment pipeline using httpx."""
import httpx
import uuid
import json
import sys

BASE = "http://localhost:8000"


def main():
    results = []

    # ── 1. Register candidate ──
    email = f"e2e-{uuid.uuid4().hex[:8]}@test.com"
    payload = {
        "name": "E2E Pipeline Tester",
        "email": email,
        "password": "Candidate@123",
        "college": "Test University",
        "branch": "CSE",
        "cgpa": 8.5,
        "passed_out_year": 2026,
        "language_choice": "python",
    }
    headers = {"Content-Type": "application/json"}
    r = httpx.post(f"{BASE}/api/auth/register", json=payload)
    assert r.status_code == 201, f"Register failed ({r.status_code}): {r.text}"
    candidate_token = r.json()["access_token"]
    results.append(f"✓ Registered candidate {email}")

    # ── 2. Verify candidate is APPLIED ──
    r = httpx.get(f"{BASE}/api/candidates/me", headers={"Authorization": f"Bearer {candidate_token}"})
    assert r.status_code == 200
    candidate_id = r.json()["id"]
    assert r.json()["status"] == "APPLIED"
    results.append(f"✓ Candidate status: APPLIED (id={candidate_id[:8]})")

    # ── 3. HR logs in and runs screening ──
    r = httpx.post(f"{BASE}/api/auth/login", json={"email": "hr@knowledgefactory.com", "password": "Hr@12345"})
    assert r.status_code == 200
    hr_token = r.json()["access_token"]
    hr_headers = {"Authorization": f"Bearer {hr_token}"}

    r = httpx.post(f"{BASE}/api/screening/run?branch=CSE", headers=hr_headers)
    assert r.status_code == 200, f"Screening failed: {r.text}"
    screen_data = r.json()
    results.append(f"✓ Screening: {screen_data['passed']} passed, {screen_data['rejected']} rejected")

    # ── 4. Verify candidate is ROUND1_PASSED ──
    r = httpx.get(f"{BASE}/api/candidates/me", headers={"Authorization": f"Bearer {candidate_token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "ROUND1_PASSED", f"Got {r.json()['status']}"
    results.append(f"✓ Candidate status after screening: ROUND1_PASSED")

    # ── 5. Start ROUND_2 assessment ──
    r = httpx.post(f"{BASE}/api/assessment/start",
                   headers={"Authorization": f"Bearer {candidate_token}"},
                   json={"round": "ROUND_2"})
    assert r.status_code == 200, f"Start assessment failed: {r.text}"
    assessment = r.json()
    assessment_id = assessment["id"]
    assert assessment["round"] == "ROUND_2"
    assert assessment["status"] == "IN_PROGRESS"
    results.append(f"✓ ROUND_2 assessment started: {assessment_id[:8]}")

    # ── 6. Verify candidate status changed to ROUND2_IN_PROGRESS ──
    r = httpx.get(f"{BASE}/api/candidates/me", headers={"Authorization": f"Bearer {candidate_token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "ROUND2_IN_PROGRESS"
    results.append(f"✓ Candidate status: ROUND2_IN_PROGRESS")

    # ── 7. Submit coding section ──
    r = httpx.post(f"{BASE}/api/assessment/submit-section",
                   headers={"Authorization": f"Bearer {candidate_token}"},
                   json={
                       "assessment_id": assessment_id,
                       "section": "CODING",
                       "content": {"code": "print('test')", "problemId": "r2_p1"},
                       "time_spent_seconds": 60,
                   })
    assert r.status_code == 200, f"Submit failed: {r.text}"
    submit_data = r.json()
    assert "submission_id" in submit_data
    results.append(f"✓ Section submitted: {submit_data['submission_id'][:8]}")

    # ── 8. Complete assessment ──
    r = httpx.post(f"{BASE}/api/assessment/{assessment_id}/complete",
                   headers={"Authorization": f"Bearer {candidate_token}"})
    assert r.status_code == 200, f"Complete failed: {r.text}"
    assert r.json()["status"] == "COMPLETED"
    results.append(f"✓ ROUND_2 assessment completed")

    # ── 9. Verify candidate status advanced to ROUND2_PASSED ──
    r = httpx.get(f"{BASE}/api/candidates/me", headers={"Authorization": f"Bearer {candidate_token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "ROUND2_PASSED", f"Got {r.json()['status']}"
    results.append(f"✓ Candidate status: ROUND2_PASSED")

    # ── 10. Start ROUND_3 assessment ──
    r = httpx.post(f"{BASE}/api/assessment/start",
                   headers={"Authorization": f"Bearer {candidate_token}"},
                   json={"round": "ROUND_3"})
    assert r.status_code == 200, f"Start ROUND_3 failed: {r.text}"
    assessment3 = r.json()
    assessment3_id = assessment3["id"]
    assert assessment3["round"] == "ROUND_3"
    assert assessment3["status"] == "IN_PROGRESS"
    results.append(f"✓ ROUND_3 assessment started: {assessment3_id[:8]}")

    # ── 11. Verify candidate status changed to ROUND3_IN_PROGRESS ──
    r = httpx.get(f"{BASE}/api/candidates/me", headers={"Authorization": f"Bearer {candidate_token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "ROUND3_IN_PROGRESS"
    results.append(f"✓ Candidate status: ROUND3_IN_PROGRESS")

    # ── 12. Submit ROUND_3 coding section ──
    r = httpx.post(f"{BASE}/api/assessment/submit-section",
                   headers={"Authorization": f"Bearer {candidate_token}"},
                   json={
                       "assessment_id": assessment3_id,
                       "section": "USECASE",
                       "content": {"answers": {"solution": "REST API"}},
                       "time_spent_seconds": 120,
                   })
    assert r.status_code == 200, f"ROUND_3 submit failed: {r.text}"
    results.append(f"✓ ROUND_3 section submitted: {r.json()['submission_id'][:8]}")

    # ── 13. Complete ROUND_3 assessment ──
    r = httpx.post(f"{BASE}/api/assessment/{assessment3_id}/complete",
                   headers={"Authorization": f"Bearer {candidate_token}"})
    assert r.status_code == 200, f"ROUND_3 complete failed: {r.text}"
    assert r.json()["status"] == "COMPLETED"
    results.append(f"✓ ROUND_3 assessment completed")

    # ── 14. Verify candidate status advanced to ROUND3_PASSED ──
    r = httpx.get(f"{BASE}/api/candidates/me", headers={"Authorization": f"Bearer {candidate_token}"})
    assert r.status_code == 200
    status = r.json()["status"]
    assert status == "ROUND3_PASSED", f"Expected ROUND3_PASSED, got {status}"
    results.append(f"✓ Candidate final status: ROUND3_PASSED")

    # ── 15. Verify pipeline stats updated ──
    r = httpx.get(f"{BASE}/api/screening/pipeline-stats", headers=hr_headers)
    assert r.status_code == 200
    stats = r.json()["stats"]
    passed_entries = {k: v for k, v in stats.items() if v > 0}
    results.append(f"✓ Pipeline stats: {json.dumps(passed_entries)}")

    print("\n=== FULL E2E PIPELINE RESULTS ===")
    for line in results:
        print(line)
    print("\n✓ ALL 15 STEPS PASSED!")


if __name__ == "__main__":
    main()
