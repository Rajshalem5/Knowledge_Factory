"""Integration tests for proctoring HTTP endpoints.

Tests the POST /api/proctoring/event endpoint end-to-end,
including record creation, event appending, and termination logic.
"""
import uuid
import pytest
from httpx import AsyncClient


class TestProctoringRoutes:
    """Test the proctoring event recording route."""

    async def _reg_candidate_and_start_assessment(
        self, client: AsyncClient, hr_headers: dict, admin_headers: dict
    ) -> tuple[str, str, str]:
        """Register a candidate, run screening, start ROUND_2, return (token, candidate_id, assessment_id)."""
        email = f"proctor-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Proctor Test", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026, "language_choice": "python",
        })
        assert reg.status_code == 201, reg.text
        c_token = reg.json()["access_token"]
        c_headers = {"Authorization": f"Bearer {c_token}"}

        # Run screening
        screen = await client.post("/api/screening/run", headers=hr_headers)
        assert screen.status_code == 200, screen.text

        # Advance to ROUND2_IN_PROGRESS
        me = await client.get("/api/candidates/me", headers=c_headers)
        cid = me.json()["id"]

        # Start ROUND_2 assessment
        asm = await client.post(
            "/api/assessment/start",
            headers=c_headers,
            json={"round": "ROUND_2"},
        )
        assert asm.status_code == 200, asm.text
        aid = asm.json()["id"]
        return c_token, cid, aid

    async def test_01_record_low_severity_event(self, client: AsyncClient):
        """A low-severity event is recorded and warning_count increments."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        hr_headers = {"Authorization": f"Bearer {hr_login.json()['access_token']}"}
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        c_token, cid, aid = await self._reg_candidate_and_start_assessment(
            client, hr_headers, admin_headers
        )
        c_headers = {"Authorization": f"Bearer {c_token}"}

        resp = await client.post(
            "/api/proctoring/event",
            headers=c_headers,
            json={
                "assessment_id": aid,
                "candidate_id": cid,
                "event_type": "tab_switch",
                "severity": "low",
                "evidence": {"detail": "Tab switched at 12:34"},
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["warning_count"] == 1
        assert data["terminated"] is False
        assert data["reason"] is None

    async def test_02_multiple_low_events_no_termination(self, client: AsyncClient):
        """Multiple low-severity events accumulate warnings without terminating."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        hr_headers = {"Authorization": f"Bearer {hr_login.json()['access_token']}"}
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        c_token, cid, aid = await self._reg_candidate_and_start_assessment(
            client, hr_headers, admin_headers
        )
        c_headers = {"Authorization": f"Bearer {c_token}"}

        # Send 2 low-severity events
        for _ in range(2):
            resp = await client.post(
                "/api/proctoring/event",
                headers=c_headers,
                json={
                    "assessment_id": aid,
                    "candidate_id": cid,
                    "event_type": "tab_switch",
                    "severity": "low",
                },
            )
            assert resp.status_code == 201

        data = resp.json()
        assert data["warning_count"] == 2
        assert data["terminated"] is False

    async def test_03_high_severity_triggers_termination(self, client: AsyncClient):
        """A single HIGH-severity event triggers immediate termination."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        hr_headers = {"Authorization": f"Bearer {hr_login.json()['access_token']}"}
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        c_token, cid, aid = await self._reg_candidate_and_start_assessment(
            client, hr_headers, admin_headers
        )
        c_headers = {"Authorization": f"Bearer {c_token}"}

        resp = await client.post(
            "/api/proctoring/event",
            headers=c_headers,
            json={
                "assessment_id": aid,
                "candidate_id": cid,
                "event_type": "multiple_faces",
                "severity": "high",
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["warning_count"] == 1
        assert data["terminated"] is True
        assert "High-severity" in (data["reason"] or "")

    async def test_04_event_missing_fields_returns_422(self, client: AsyncClient):
        """Missing required fields results in a 422 validation error."""
        # Register a candidate to get a valid candidate token
        email = f"proctor-missing-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Proctor Missing", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026, "language_choice": "python",
        })
        assert reg.status_code == 201, reg.text
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        resp = await client.post(
            "/api/proctoring/event",
            headers=headers,
            json={
                # Missing assessment_id and candidate_id
                "event_type": "tab_switch",
            },
        )
        assert resp.status_code == 422, resp.text

    async def test_05_event_requires_auth(self, client: AsyncClient):
        """Unauthenticated requests get 401."""
        resp = await client.post(
            "/api/proctoring/event",
            json={
                "assessment_id": "test",
                "candidate_id": "test",
                "event_type": "tab_switch",
            },
        )
        assert resp.status_code == 401, resp.text
