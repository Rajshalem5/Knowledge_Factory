"""Integration tests for selection routes.

Tests select/reject/bulk-select endpoints and status transitions.
"""
import uuid
import pytest
from httpx import AsyncClient


class TestSelectionRoutes:
    """Test candidate selection/rejection workflow."""

    async def _admin_headers(self, client: AsyncClient) -> dict:
        resp = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert resp.status_code == 200
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def _hr_headers(self, client: AsyncClient) -> dict:
        resp = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert resp.status_code == 200
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def _register_and_advance_to_interview_completed(
        self, client: AsyncClient, admin_headers: dict, hr_headers: dict
    ) -> str:
        """Register candidate and advance through all stages to INTERVIEW_COMPLETED."""
        # Register
        email = f"sel-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Selection Test", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026, "language_choice": "python",
        })
        assert reg.status_code == 201
        c_token = reg.json()["access_token"]
        c_headers = {"Authorization": f"Bearer {c_token}"}

        # Get candidate ID
        me = await client.get("/api/candidates/me", headers=c_headers)
        assert me.status_code == 200
        c_id = me.json()["id"]

        # Screen
        await client.post("/api/screening/run", headers=hr_headers)

        # Advance through pipeline
        transitions = [
            "ROUND2_IN_PROGRESS", "ROUND2_PASSED",
            "ROUND3_IN_PROGRESS", "ROUND3_PASSED",
            "INTERVIEW_SCHEDULED",
        ]
        for target in transitions:
            resp = await client.patch(
                f"/api/candidates/{c_id}/status",
                headers=admin_headers,
                json={"status": target},
            )
            assert resp.status_code == 200, f"Transition to {target} failed: {resp.text}"

        # Submit interview feedback to move to INTERVIEW_COMPLETED
        fb = await client.post(
            f"/api/candidates/{c_id}/feedback",
            headers=admin_headers,
            json={"technicalScore": 8, "communicationScore": 7, "recommendation": "SELECT", "notes": "Good"},
        )
        assert fb.status_code == 201
        return c_id

    async def test_01_select_candidate(self, client: AsyncClient):
        """Test: HR can select an INTERVIEW_COMPLETED candidate."""
        admin_hdrs = await self._admin_headers(client)
        hr_hdrs = await self._hr_headers(client)
        c_id = await self._register_and_advance_to_interview_completed(client, admin_hdrs, hr_hdrs)

        # Select the candidate
        resp = await client.post(
            f"/api/selection/candidates/{c_id}/select",
            headers=hr_hdrs,
        )
        assert resp.status_code == 200, f"Select failed: {resp.text}"
        assert resp.json()["status"] == "SELECTED"

    async def test_02_select_nonexistent_candidate(self, client: AsyncClient):
        """Test: Selecting a non-existent candidate returns 404."""
        hr_hdrs = await self._hr_headers(client)
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/selection/candidates/{fake_id}/select",
            headers=hr_hdrs,
        )
        assert resp.status_code == 404

    async def test_03_select_candidate_invalid_status(self, client: AsyncClient):
        """Test: Selecting a candidate in APPLIED status returns 422."""
        hr_hdrs = await self._hr_headers(client)

        # Register applicant (stays APPLIED)
        email = f"sel-inv-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Invalid Select", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026,
        })
        assert reg.status_code == 201
        c_token = reg.json()["access_token"]
        me = await client.get("/api/candidates/me", headers={"Authorization": f"Bearer {c_token}"})
        c_id = me.json()["id"]

        # Try selecting APPLIED candidate (should fail)
        resp = await client.post(
            f"/api/selection/candidates/{c_id}/select",
            headers=hr_hdrs,
        )
        assert resp.status_code == 422
        assert "Cannot select" in resp.json()["detail"]

    async def test_04_reject_candidate(self, client: AsyncClient):
        """Test: HR can reject a candidate."""
        admin_hdrs = await self._admin_headers(client)
        hr_hdrs = await self._hr_headers(client)
        c_id = await self._register_and_advance_to_interview_completed(client, admin_hdrs, hr_hdrs)

        resp = await client.post(
            f"/api/selection/candidates/{c_id}/reject",
            headers=hr_hdrs,
            params={"reason": "Not a fit for current openings"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"

    async def test_05_reject_nonexistent_candidate(self, client: AsyncClient):
        """Test: Rejecting a non-existent candidate returns 404."""
        hr_hdrs = await self._hr_headers(client)
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/selection/candidates/{fake_id}/reject",
            headers=hr_hdrs,
        )
        assert resp.status_code == 404

    async def test_06_bulk_select(self, client: AsyncClient):
        """Test: Bulk select endpoint processes multiple candidates."""
        admin_hdrs = await self._admin_headers(client)
        hr_hdrs = await self._hr_headers(client)

        # Create two interview-completed candidates
        c1 = await self._register_and_advance_to_interview_completed(client, admin_hdrs, hr_hdrs)
        c2 = await self._register_and_advance_to_interview_completed(client, admin_hdrs, hr_hdrs)

        # Bulk select
        resp = await client.post(
            "/api/selection/candidates/bulk-select",
            headers=hr_hdrs,
            json=[{"candidate_id": c1}, {"candidate_id": c2}],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["status"] == "selected"
        assert data["results"][1]["status"] == "selected"

    async def test_07_bulk_select_with_invalid_id(self, client: AsyncClient):
        """Test: Bulk select with an invalid candidate ID returns error for that entry."""
        hr_hdrs = await self._hr_headers(client)
        fake_id = str(uuid.uuid4())

        resp = await client.post(
            "/api/selection/candidates/bulk-select",
            headers=hr_hdrs,
            json=[{"candidate_id": fake_id}],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"][0]["error"] is not None
