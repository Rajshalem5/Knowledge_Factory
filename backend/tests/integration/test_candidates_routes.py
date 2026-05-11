"""Integration tests for candidate routes edge cases.

Tests GET /me, GET /{id}, PATCH /{id}/status, bulk upload, and auth guards.
"""
import uuid
import pytest
from httpx import AsyncClient


class TestCandidatesRoutes:
    """Test candidate CRUD operations and edge cases."""

    async def _admin_headers(self, client: AsyncClient) -> dict:
        resp = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert resp.status_code == 200
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def _register_candidate(self, client: AsyncClient) -> tuple[str, str]:
        """Register a candidate and return (token, candidate_id)."""
        email = f"cand-edge-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Edge Case", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026, "language_choice": "python",
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        me = await client.get("/api/candidates/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        return token, me.json()["id"]

    async def test_01_get_my_profile(self, client: AsyncClient):
        """Test: Authenticated candidate can GET /me."""
        token, cid = await self._register_candidate(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get("/api/candidates/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == cid
        assert data["status"] is not None
        assert "display_status" in data
        assert data["display_status"] == "applied"
        assert "scores" in data
        assert "interview_feedback" in data

    async def test_02_get_my_profile_without_auth(self, client: AsyncClient):
        """Test: Unauthenticated request to /me returns 401."""
        resp = await client.get("/api/candidates/me")
        assert resp.status_code == 401

    async def test_03_get_candidate_by_id(self, client: AsyncClient):
        """Test: Admin can GET a candidate by ID."""
        admin_hdrs = await self._admin_headers(client)
        token, cid = await self._register_candidate(client)

        resp = await client.get(f"/api/candidates/{cid}", headers=admin_hdrs)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == cid
        assert data["name"] == "Edge Case"
        assert "phone" in data
        assert "cycle_id" in data

    async def test_04_get_candidate_not_found(self, client: AsyncClient):
        """Test: Getting a non-existent candidate returns 404."""
        admin_hdrs = await self._admin_headers(client)
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/api/candidates/{fake_id}", headers=admin_hdrs)
        assert resp.status_code == 404

    async def test_05_get_candidate_without_auth(self, client: AsyncClient):
        """Test: Unauthenticated request returns 401."""
        resp = await client.get(f"/api/candidates/{uuid.uuid4()}")
        assert resp.status_code == 401

    async def test_06_update_status_valid_transition(self, client: AsyncClient):
        """Test: Admin can update candidate status via valid FSM transition."""
        admin_hdrs = await self._admin_headers(client)
        hr_resp = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        hr_headers = {"Authorization": f"Bearer {hr_resp.json()['access_token']}"}

        token, cid = await self._register_candidate(client)

        # Screen first (moves APPLIED -> ROUND1_PASSED)
        screen = await client.post("/api/screening/run", headers=hr_headers)
        assert screen.status_code == 200
        assert screen.json()["passed"] >= 1

        # Now valid transition: ROUND1_PASSED -> ROUND2_IN_PROGRESS
        resp = await client.patch(
            f"/api/candidates/{cid}/status",
            headers=admin_hdrs,
            json={"status": "ROUND2_IN_PROGRESS"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ROUND2_IN_PROGRESS"

    async def test_07_update_status_invalid_transition(self, client: AsyncClient):
        """Test: Invalid FSM transition returns 422."""
        admin_hdrs = await self._admin_headers(client)
        token, cid = await self._register_candidate(client)

        # Try to go from APPLIED directly to SELECTED (invalid)
        resp = await client.patch(
            f"/api/candidates/{cid}/status",
            headers=admin_hdrs,
            json={"status": "SELECTED"},
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    async def test_08_update_status_invalid_value(self, client: AsyncClient):
        """Test: Invalid status string returns 422."""
        admin_hdrs = await self._admin_headers(client)
        token, cid = await self._register_candidate(client)

        resp = await client.patch(
            f"/api/candidates/{cid}/status",
            headers=admin_hdrs,
            json={"status": "INVALID_STATUS_HERE"},
        )
        assert resp.status_code == 422

    async def test_09_update_status_not_found(self, client: AsyncClient):
        """Test: Updating a non-existent candidate returns 404."""
        admin_hdrs = await self._admin_headers(client)
        fake_id = str(uuid.uuid4())
        resp = await client.patch(
            f"/api/candidates/{fake_id}/status",
            headers=admin_hdrs,
            json={"status": "ROUND1_PASSED"},
        )
        assert resp.status_code == 404

    async def test_10_update_status_unauthorized(self, client: AsyncClient):
        """Test: Candidate cannot update own status."""
        token, cid = await self._register_candidate(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.patch(
            f"/api/candidates/{cid}/status",
            headers=headers,
            json={"status": "ROUND1_PASSED"},
        )
        assert resp.status_code == 403

    async def test_11_list_candidates(self, client: AsyncClient):
        """Test: HR can list candidates with pagination."""
        hr_resp = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        hr_headers = {"Authorization": f"Bearer {hr_resp.json()['access_token']}"}

        resp = await client.get("/api/candidates/?page=1&limit=10", headers=hr_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10
        assert isinstance(data["data"], list)

    async def test_12_list_candidates_filter_by_branch(self, client: AsyncClient):
        """Test: Candidates list can be filtered by branch."""
        hr_resp = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        hr_headers = {"Authorization": f"Bearer {hr_resp.json()['access_token']}"}

        resp = await client.get("/api/candidates/?branch=CSE&limit=100", headers=hr_headers)
        assert resp.status_code == 200
        data = resp.json()
        for c in data["data"]:
            assert "CSE" in c["branch"].upper()

    async def test_13_bulk_upload_no_file(self, client: AsyncClient):
        """Test: Bulk upload without a file returns 400."""
        hr_resp = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        hr_headers = {"Authorization": f"Bearer {hr_resp.json()['access_token']}"}

        resp = await client.post("/api/candidates/bulk-upload", headers=hr_headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
