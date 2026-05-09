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


class TestAPIConsistency:
    """Test API response consistency."""

    async def test_01_basic_auth_flow(self, client: AsyncClient):
        """Test basic login returns proper structure."""
        response = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        # Should succeed since we seed the admin user
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@knowledgefactory.io"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
