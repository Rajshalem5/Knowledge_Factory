"""Integration tests for hiring cycle routes.

Tests CRUD operations for hiring cycles.
"""
import pytest
from httpx import AsyncClient


class TestHiringCycles:
    """Test hiring cycle CRUD routes."""

    async def _admin_headers(self, client: AsyncClient) -> dict:
        resp = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert resp.status_code == 200
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def test_01_list_cycles(self, client: AsyncClient):
        """Test: List hiring cycles returns the seeded cycle."""
        headers = await self._admin_headers(client)
        resp = await client.get("/api/hiring-cycles/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        cycle = data[0]
        assert "id" in cycle
        assert "name" in cycle
        assert "start_date" in cycle
        assert "end_date" in cycle
        assert "status" in cycle
        assert "eligibility_config" in cycle
        assert "created_at" in cycle

    async def test_02_list_cycles_without_auth(self, client: AsyncClient):
        """Test: Unauthenticated request returns 401."""
        resp = await client.get("/api/hiring-cycles/")
        assert resp.status_code == 401

    async def test_03_list_cycles_as_candidate(self, client: AsyncClient):
        """Test: Candidate cannot list cycles."""
        import uuid
        email = f"cycle-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Cycle Test", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026,
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get("/api/hiring-cycles/", headers=headers)
        assert resp.status_code == 403

    async def test_04_create_cycle(self, client: AsyncClient):
        """Test: Admin can create a new hiring cycle."""
        headers = await self._admin_headers(client)
        resp = await client.post("/api/hiring-cycles/", headers=headers, json={
            "name": "Test Cycle New",
            "start_date": "2026-06-01",
            "end_date": "2026-12-31",
            "eligibility_config": {"min_cgpa": 7.0, "allowed_branches": ["CSE", "IT"]},
        })
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "id" in data
        assert data["name"] == "Test Cycle New"

        # Verify it appears in the list
        list_resp = await client.get("/api/hiring-cycles/", headers=headers)
        names = [c["name"] for c in list_resp.json()]
        assert "Test Cycle New" in names

    async def test_05_create_cycle_requires_admin(self, client: AsyncClient):
        """Test: HR cannot create a new hiring cycle."""
        hr_resp = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_resp.status_code == 200
        hr_headers = {"Authorization": f"Bearer {hr_resp.json()['access_token']}"}
        resp = await client.post("/api/hiring-cycles/", headers=hr_headers, json={
            "name": "HR Cycle",
            "start_date": "2026-06-01",
            "end_date": "2026-12-31",
        })
        assert resp.status_code == 403

    async def test_06_update_cycle(self, client: AsyncClient):
        """Test: Admin can update an existing hiring cycle."""
        headers = await self._admin_headers(client)

        # Create a cycle first
        create = await client.post("/api/hiring-cycles/", headers=headers, json={
            "name": "Cycle To Update",
            "start_date": "2026-06-01",
            "end_date": "2026-12-31",
        })
        assert create.status_code == 201
        cycle_id = create.json()["id"]

        # Update the cycle name
        resp = await client.patch(
            f"/api/hiring-cycles/{cycle_id}",
            headers=headers,
            json={"name": "Updated Cycle Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Cycle updated"

        # Verify update took effect
        list_resp = await client.get("/api/hiring-cycles/", headers=headers)
        updated = [c for c in list_resp.json() if c["id"] == cycle_id]
        assert len(updated) == 1
        assert updated[0]["name"] == "Updated Cycle Name"

    async def test_07_update_cycle_not_found(self, client: AsyncClient):
        """Test: Updating a non-existent cycle returns 404."""
        import uuid
        headers = await self._admin_headers(client)
        fake_id = str(uuid.uuid4())
        resp = await client.patch(
            f"/api/hiring-cycles/{fake_id}",
            headers=headers,
            json={"name": "Ghost"},
        )
        assert resp.status_code == 404
