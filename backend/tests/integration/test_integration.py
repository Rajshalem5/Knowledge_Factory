"""Integration tests for complete user flows.

This file systematically tests Candidate and HR workflows to identify bugs.
Run with: pytest backend/tests/integration/test_integration.py -v
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestCandidateFlow:
    """Test complete candidate workflow."""

    async def test_01_candidate_registration(self, client: AsyncClient):
        """Test: Register new candidate -> should succeed."""
        import uuid
        unique_email = f"candidate-{uuid.uuid4().hex[:8]}@example.com"

        registration_data = {
            "name": "Test Candidate",
            "email": unique_email,
            "password": "Candidate@123",
            "college": "Test University",
            "branch": "Computer Science",
            "cgpa": 8.5,
            "passed_out_year": 2026,
            "language_choice": "english",
        }

        response = await client.post("/api/auth/register", json=registration_data)

        # ASSERT: Should return 201 Created
        assert response.status_code == 201, f"Registration failed: {response.text}"

        # ASSERT: Response should contain access_token
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        assert "refresh_token" in data, "Response missing refresh_token"
        assert "user" in data, "Response missing user object"

        # ASSERT: User object is well-formed
        user = data["user"]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "role" in user

        print(f"✓ Registration successful for {registration_data['email']}")

    async def test_02_candidate_login(self, client: AsyncClient):
        """Test: Login with registered candidate credentials."""
        import uuid
        unique_email = f"login-{uuid.uuid4().hex[:8]}@test.com"

        # First register
        register_response = await client.post(
            "/api/auth/register",
            json={
                "name": "Login Test Candidate",
                "email": unique_email,
                "password": "Candidate@123",
                "college": "Test College",
                "branch": "IT",
                "cgpa": 9.0,
                "passed_out_year": 2026,
            },
        )
        assert register_response.status_code == 201

        # Then login
        response = await client.post(
            "/api/auth/login",
            json={
                "email": unique_email,
                "password": "Candidate@123"
            },
        )

        # ASSERT: Login should succeed
        assert response.status_code == 200, f"Login failed: {response.text}"

        # ASSERT: Token structure correct
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "CANDIDATE"

        print("✓ Candidate login successful")

    async def test_03_get_me_endpoint(self, client: AsyncClient):
        """Test: Get current authenticated user."""
        # Login as admin
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        # ASSERT: Should return user info
        assert response.status_code == 200

        data = response.json()
        print(f"Current user: {data}")

        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "role" in data

        print("✓ /api/auth/me works correctly")

    async def test_04_screening_pipeline(self, client: AsyncClient):
        """Test: Run screening via pipeline endpoint."""
        # Login as admin
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Run screening
        response = await client.post("/api/screening/run", headers=headers)

        print(f"Screening response: {response.status_code} - {response.text}")

        # Should succeed with valid data
        assert response.status_code == 200

        data = response.json()
        assert "screened" in data
        assert "passed" in data
        assert "rejected" in data

        # CSE candidate with 8.5 CGPA should pass
        # CSE candidate with 5.5 CGPA should fail (CGPA < 6.0)
        # CIVIL candidate with 7.5 should fail (wrong branch)
        assert data["passed"] >= 1
        assert data["rejected"] >= 1

        print(f"✓ Screening pipeline works: {data}")

    async def test_05_pipeline_stats(self, client: AsyncClient):
        """Test: Get pipeline statistics with filters."""
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get pipeline stats
        response = await client.get("/api/screening/pipeline-stats", headers=headers)

        print(f"Pipeline stats response: {response.status_code} - {response.text}")
        assert response.status_code == 200

        data = response.json()
        assert "stats" in data

        # All statuses should be present
        from app.core.enums import CandidateStatus
        for s in CandidateStatus:
            assert s.value in data["stats"], f"Missing status: {s.value}"

        print("✓ Pipeline stats retrieved successfully")

    async def test_06_pipeline_stats_with_filters(self, client: AsyncClient):
        """Test: Pipeline stats with extra filters."""
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test branch filter
        response = await client.get(
            "/api/screening/pipeline-stats?branch=CSE",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Branch-filtered stats: {data}")
        assert "stats" in data

        # Test search filter
        response = await client.get(
            "/api/screening/pipeline-stats?search=applied",
            headers=headers,
        )
        assert response.status_code == 200
        print(f"Search-filtered stats: {response.json()}")

        print("✓ Pipeline stats with filters work correctly")


class TestEnhancedPipelineFilters:
    """Test enhanced filtering features on the pipeline."""

    async def test_01_screening_with_passed_out_year_range(self, client: AsyncClient):
        """Test: Screening with passed_out_year_min/max range filters."""
        import uuid

        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Register a candidate with passed_out_year=2025
        email = f"range-{uuid.uuid4().hex[:8]}@test.com"
        await client.post(
            "/api/auth/register",
            json={
                "name": "Range Test", "email": email, "password": "Candidate@123",
                "college": "Mid Uni", "branch": "CSE", "cgpa": 7.0,
                "passed_out_year": 2025, "language_choice": "python",
            },
        )

        # Screen with passed_out_year_min=2024 — should include the 2025 candidate
        response = await client.post(
            "/api/screening/run?passed_out_year_min=2024",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"passed_out_year_min=2024 screening: {data}")
        assert data["screened"] >= 1, "Should have screened at least the 2025 candidate"

        # Register another candidate with passed_out_year=2022
        email2 = f"range2-{uuid.uuid4().hex[:8]}@test.com"
        await client.post(
            "/api/auth/register",
            json={
                "name": "Range Test 2", "email": email2, "password": "Candidate@123",
                "college": "Old Uni", "branch": "ECE", "cgpa": 7.5,
                "passed_out_year": 2022, "language_choice": "java",
            },
        )

        # Screen with passed_out_year_max=2023 — should only include the 2022 candidate
        response2 = await client.post(
            "/api/screening/run?passed_out_year_max=2023",
            headers=headers,
        )
        assert response2.status_code == 200
        data2 = response2.json()
        print(f"passed_out_year_max=2023 screening: {data2}")
        # The 2022 candidate (ECE, 7.5) should pass (branch allowed, cgpa >= 6.0)
        assert data2["screened"] >= 1, "Should have screened the 2022 candidate"

        print("✓ Screening with passed_out_year range filters works")

    async def test_02_pipeline_stats_with_cgpa_filters(self, client: AsyncClient):
        """Test: Pipeline stats with cgpa_min and cgpa_max filters."""
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Stats filtered by cgpa_min=8.0
        response = await client.get(
            "/api/screening/pipeline-stats?cgpa_min=8.0",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"CGPA min=8.0 stats: {data}")
        assert "stats" in data

        # Stats filtered by cgpa_max=6.0
        response = await client.get(
            "/api/screening/pipeline-stats?cgpa_max=6.0",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"CGPA max=6.0 stats: {data}")
        assert "stats" in data

        print("✓ Pipeline stats with CGPA filters work correctly")

    async def test_03_screening_with_email_verified_filter(self, client: AsyncClient):
        """Test: Screening with email_verified filter."""
        import uuid

        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Register a candidate
        email = f"emailvfy-{uuid.uuid4().hex[:8]}@test.com"
        await client.post(
            "/api/auth/register",
            json={
                "name": "Email Vfy", "email": email, "password": "Candidate@123",
                "college": "Test Uni", "branch": "CSE", "cgpa": 8.0,
                "passed_out_year": 2026, "language_choice": "python",
            },
        )

        # Screen with email_verified=false — should still screen since new reg has email_verified=false
        response = await client.post(
            "/api/screening/run?email_verified=false",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"email_verified=false screening: {data}")
        assert "passed" in data
        assert "rejected" in data

        # Screen with email_verified=true — should skip unverified candidates
        response2 = await client.post(
            "/api/screening/run?email_verified=true",
            headers=headers,
        )
        assert response2.status_code == 200
        data2 = response2.json()
        print(f"email_verified=true screening: {data2}")

        print("✓ Screening with email_verified filter works")

    async def test_04_pipeline_stats_with_target_statuses(self, client: AsyncClient):
        """Test: Pipeline stats with target_statuses filter (multi-status output selection)."""
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Request only specific statuses in the output
        response = await client.get(
            "/api/screening/pipeline-stats?target_statuses=APPLIED,ROUND1_PASSED,SELECTED",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"target_statuses=APPLIED,ROUND1_PASSED,SELECTED stats: {data}")
        assert "stats" in data
        # Only the requested statuses should appear
        assert "APPLIED" in data["stats"]
        assert "ROUND1_PASSED" in data["stats"]
        assert "SELECTED" in data["stats"]
        # Statuses not in the target list should not appear
        assert "ROUND2_IN_PROGRESS" not in data["stats"]

        # Test with a single target status
        response2 = await client.get(
            "/api/screening/pipeline-stats?target_statuses=APPLIED",
            headers=headers,
        )
        assert response2.status_code == 200
        data2 = response2.json()
        print(f"target_statuses=APPLIED stats: {data2}")
        assert len(data2["stats"]) == 1
        assert "APPLIED" in data2["stats"]

        print("✓ Pipeline stats with target_statuses filter works")

    async def test_05_funnel_with_target_statuses(self, client: AsyncClient):
        """Test: Funnel with target_statuses filter."""
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Request only specific funnel stages
        response = await client.get(
            "/api/analytics/funnel?target_statuses=applied,selected",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        print(f"target_statuses=applied,selected funnel: {data}")
        # Only requested stages should appear
        assert "applied" in data
        assert "selected" in data
        # Stages not in the target list should not appear
        assert "eligible" not in data
        assert "assessed" not in data

        print("✓ Funnel with target_statuses filter works")


class TestFullPipelineE2E:
    """Test the complete screening-to-assessment pipeline end-to-end."""

    async def test_01_full_pipeline_with_filters(self, client: AsyncClient):
        """Test: Complete pipeline: register → screening with filters → assessment start → submit → complete."""
        import uuid

        # ── 1. Register a new candidate ──
        email = f"e2e-pipe-{uuid.uuid4().hex[:8]}@test.com"
        reg_resp = await client.post(
            "/api/auth/register",
            json={
                "name": "E2E Pipe Candidate", "email": email, "password": "Candidate@123",
                "college": "Test University", "branch": "CSE", "cgpa": 8.5,
                "passed_out_year": 2026, "language_choice": "python",
            },
        )
        assert reg_resp.status_code == 201
        candidate_token = reg_resp.json()["access_token"]

        # ── 2. Verify candidate is APPLIED ──
        me_resp = await client.get(
            "/api/candidates/me",
            headers={"Authorization": f"Bearer {candidate_token}"},
        )
        assert me_resp.status_code == 200
        candidate_id = me_resp.json()["id"]
        assert me_resp.json()["status"] == "APPLIED"
        print(f"✓ Candidate registered: {candidate_id} (APPLIED)")

        # ── 3. HR logs in and runs screening ──
        hr_login = await client.post(
            "/api/auth/login",
            json={"email": "hr@knowledgefactory.com", "password": "Hr@12345"},
        )
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Run screening with branch filter
        screen_resp = await client.post(
            "/api/screening/run?branch=CSE",
            headers=hr_headers,
        )
        assert screen_resp.status_code == 200
        screen_data = screen_resp.json()
        print(f"✓ Screening with branch=CSE: {screen_data}")
        assert screen_data["passed"] >= 1

        # ── 4. Verify candidate is now ROUND1_PASSED ──
        me2_resp = await client.get(
            "/api/candidates/me",
            headers={"Authorization": f"Bearer {candidate_token}"},
        )
        assert me2_resp.status_code == 200
        assert me2_resp.json()["status"] == "ROUND1_PASSED"
        print("✓ Candidate status after screening: ROUND1_PASSED")

        # ── 5. Start ROUND_2 assessment ──
        start_resp = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {candidate_token}"},
            json={"round": "ROUND_2"},
        )
        assert start_resp.status_code == 200
        assessment = start_resp.json()
        assessment_id = assessment["id"]
        assert assessment["round"] == "ROUND_2"
        assert assessment["status"] == "IN_PROGRESS"
        print(f"✓ Assessment started: {assessment_id}")

        # ── 6. Verify candidate status changed to ROUND2_IN_PROGRESS ──
        me3_resp = await client.get(
            "/api/candidates/me",
            headers={"Authorization": f"Bearer {candidate_token}"},
        )
        assert me3_resp.status_code == 200
        assert me3_resp.json()["status"] == "ROUND2_IN_PROGRESS"
        print("✓ Candidate status after assessment start: ROUND2_IN_PROGRESS")

        # ── 7. Submit coding section ──
        submit_resp = await client.post(
            "/api/assessment/submit-section",
            headers={"Authorization": f"Bearer {candidate_token}"},
            json={
                "assessment_id": assessment_id,
                "section": "CODING",
                "content": {"code": "print('test')", "problemId": "r2_p1"},
                "time_spent_seconds": 60,
            },
        )
        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        assert "submission_id" in submit_data
        print(f"✓ Section submitted: {submit_data['submission_id']}")

        # ── 8. Complete assessment ──
        complete_resp = await client.post(
            f"/api/assessment/{assessment_id}/complete",
            headers={"Authorization": f"Bearer {candidate_token}"},
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["status"] == "COMPLETED"
        print("✓ Assessment completed")

        # ── 9. Verify candidate status advanced to ROUND2_PASSED ──
        me4_resp = await client.get(
            "/api/candidates/me",
            headers={"Authorization": f"Bearer {candidate_token}"},
        )
        assert me4_resp.status_code == 200
        assert me4_resp.json()["status"] == "ROUND2_PASSED"
        print("✓ Candidate status after completion: ROUND2_PASSED")

        # ── 10. Verify pipeline stats updated ──
        stats_resp = await client.get(
            "/api/screening/pipeline-stats",
            headers=hr_headers,
        )
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        print(f"✓ Pipeline stats: {stats}")
        assert int(stats["stats"].get("ROUND2_PASSED", 0)) >= 1

        print("\n✓ FULL PIPELINE E2E WITH FILTERS PASSED!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
