"""Integration tests for admin routes.

Tests user listing and organization endpoints.
"""
import pytest
from httpx import AsyncClient


class TestAdminUsers:
    """Test admin user management routes."""

    async def _auth_headers(self, client: AsyncClient, email: str, password: str) -> dict:
        resp = await client.post("/api/auth/login", json={
            "email": email, "password": password,
        })
        assert resp.status_code == 200
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def test_01_list_users_as_admin(self, client: AsyncClient):
        """Test: Admin can list platform users."""
        headers = await self._auth_headers(client, "admin@knowledgefactory.io", "Admin@12345")
        resp = await client.get("/api/admin/users", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Each user should have expected fields
        user = data[0]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "role" in user
        assert "status" in user
        assert "created_at" in user

    async def test_02_list_users_pagination(self, client: AsyncClient):
        """Test: Users list respects pagination params."""
        headers = await self._auth_headers(client, "admin@knowledgefactory.io", "Admin@12345")
        resp = await client.get("/api/admin/users?page=1&limit=1", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) <= 1

    async def test_03_list_users_unauthorized(self, client: AsyncClient):
        """Test: Candidate cannot list users (should get 401/403)."""
        import uuid
        email = f"unauth-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Unauth Test", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026,
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get("/api/admin/users", headers=headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"

    async def test_04_list_users_without_auth(self, client: AsyncClient):
        """Test: Unauthenticated request returns 401."""
        resp = await client.get("/api/admin/users")
        assert resp.status_code == 401

    async def test_05_organizations_deprecated(self, client: AsyncClient):
        """Test: /api/admin/organizations returns empty list for backward compat."""
        resp = await client.get("/api/admin/organizations")
        assert resp.status_code == 200
        assert resp.json() == []
