"""Integration tests for audit log routes.

Tests list_audit_logs endpoint including auth enforcement,
entity_type filtering, and pagination. Mounted at /api/admin/logs.

Since the audit middleware is a Phase 2 placeholder (no automatic audit
logging), we seed audit log entries directly via the shared db_session.
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.audit.models import AuditLog


class TestAuditLogs:
    """Test the GET /api/admin/logs endpoint."""

    BASE = "/api/admin/logs"

    async def _login_admin(self, client: AsyncClient) -> str:
        resp = await client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _login_hr(self, client: AsyncClient) -> str:
        resp = await client.post(
            "/api/auth/login",
            json={"email": "hr@knowledgefactory.com", "password": "Hr@12345"},
        )
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _seed_log(
        self, db_session: AsyncSession, action: str = "create",
        entity_type: str = "candidate",
    ) -> str:
        """Insert a test audit log entry and return its ID."""
        log_id = str(uuid.uuid4())
        log = AuditLog(
            id=log_id,
            actor_id=str(uuid.uuid4()),
            action=action,
            entity_type=entity_type,
            entity_id=str(uuid.uuid4()),
            before_json={},
            after_json={"name": "Test"},
            ip_address="127.0.0.1",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(log)
        await db_session.flush()
        return log_id

    async def test_01_list_logs_requires_admin_role(self, client: AsyncClient):
        """HR users cannot list audit logs (admin-only)."""
        hr_token = await self._login_hr(client)
        resp = await client.get(
            self.BASE,
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 403

    async def test_02_list_logs_returns_paginated_results(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Admin can list audit logs with pagination metadata."""
        await self._seed_log(db_session, action="register", entity_type="candidate")
        await self._seed_log(db_session, action="update", entity_type="assessment")

        admin_token = await self._login_admin(client)
        headers = {"Authorization": f"Bearer {admin_token}"}

        resp = await client.get(f"{self.BASE}?limit=10", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2

        entry = data["data"][0]
        assert "id" in entry
        assert "action" in entry
        assert "entity_type" in entry
        assert "created_at" in entry

    async def test_03_list_logs_with_entity_type_filter(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Filter audit logs by entity_type."""
        await self._seed_log(db_session, action="create", entity_type="candidate")
        await self._seed_log(db_session, action="create", entity_type="assessment")
        await self._seed_log(db_session, action="login", entity_type="auth")

        admin_token = await self._login_admin(client)
        headers = {"Authorization": f"Bearer {admin_token}"}

        resp = await client.get(
            f"{self.BASE}?entity_type=candidate&limit=100",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) >= 1
        for entry in data["data"]:
            assert entry["entity_type"] == "candidate"

    async def test_04_list_logs_pagination_works(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Pagination properly limits results."""
        for i in range(5):
            await self._seed_log(db_session, action=f"action_{i}")

        admin_token = await self._login_admin(client)
        headers = {"Authorization": f"Bearer {admin_token}"}

        resp = await client.get(f"{self.BASE}?page=1&limit=2", headers=headers)
        assert resp.status_code == 200
        page1 = resp.json()
        assert len(page1["data"]) == 2
        assert page1["pagination"]["total"] >= 5

    async def test_05_unauthorized_access_returns_401(self, client: AsyncClient):
        """No auth token returns 401."""
        resp = await client.get(self.BASE)
        assert resp.status_code == 401

    async def test_06_empty_for_nonexistent_entity_type(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Filtering by nonexistent entity type returns empty results."""
        await self._seed_log(db_session, action="test", entity_type="candidate")

        admin_token = await self._login_admin(client)
        headers = {"Authorization": f"Bearer {admin_token}"}

        resp = await client.get(
            f"{self.BASE}?entity_type=nonexistent_xyz",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0
