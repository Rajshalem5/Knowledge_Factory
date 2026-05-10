"""Integration tests for assessment routes.

Tests start, get-by-id, submit-section, and complete endpoints
with both happy-path and edge-case scenarios.
"""

import uuid
import pytest
from httpx import AsyncClient


class TestAssessmentRoutes:
    """Test assessment CRUD and lifecycle."""

    async def _reg_candidate(self, client: AsyncClient) -> tuple[str, str]:
        """Register a candidate and return (token, candidate_id)."""
        email = f"asm-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Assessment Test", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026, "language_choice": "python",
        })
        assert reg.status_code == 201, reg.text
        token = reg.json()["access_token"]
        me = await client.get("/api/candidates/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        return token, me.json()["id"]

    async def _screen_and_pass(self, client: AsyncClient) -> str:
        """Screen all APPLIED candidates as HR and return HR token."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}
        resp = await client.post("/api/screening/run", headers=hr_headers)
        assert resp.status_code == 200
        return hr_token

    async def test_01_start_assessment_invalid_round(self, client: AsyncClient):
        """Test: Starting assessment with an invalid round value returns 422."""
        token, _ = await self._reg_candidate(client)
        await self._screen_and_pass(client)

        resp = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_4"},
        )
        # Expect 422 validation error for invalid enum
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    async def test_02_start_assessment_not_eligible(self, client: AsyncClient):
        """Test: Starting ROUND_2 without being ROUND1_PASSED returns 400."""
        token, _ = await self._reg_candidate(client)
        # Candidate is still APPLIED, try to start ROUND_2
        resp = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        assert "must be in" in resp.json()["detail"].lower()

    async def test_03_start_assessment_twice_returns_existing(self, client: AsyncClient):
        """Test: Starting the same round twice returns the existing assessment."""
        token, _ = await self._reg_candidate(client)
        await self._screen_and_pass(client)

        # First start
        r1 = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        assert r1.status_code == 200
        aid1 = r1.json()["id"]

        # Second start — status is already ROUND2_IN_PROGRESS, so it returns
        # 400 because the candidate is no longer in ROUND1_PASSED state
        r2 = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        assert r2.status_code == 400, (
            f"Expected 400 because candidate is already ROUND2_IN_PROGRESS, "
            f"got {r2.status_code}: {r2.text}"
        )

    async def test_04_get_assessment_by_id(self, client: AsyncClient):
        """Test: Get a single assessment by its ID."""
        token, _ = await self._reg_candidate(client)
        await self._screen_and_pass(client)

        start = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        assert start.status_code == 200
        assessment_id = start.json()["id"]

        # Get by ID
        resp = await client.get(
            f"/api/assessment/{assessment_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == assessment_id
        assert data["round"] == "ROUND_2"
        assert data["status"] == "IN_PROGRESS"
        assert "questions_json" in data
        assert "problems" in data["questions_json"]

    async def test_05_get_assessment_not_found(self, client: AsyncClient):
        """Test: Get a non-existent assessment returns 404."""
        token, _ = await self._reg_candidate(client)
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/assessment/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_06_get_active_assessments(self, client: AsyncClient):
        """Test: GET /api/assessment/active returns in-progress assessments."""
        token, _ = await self._reg_candidate(client)
        await self._screen_and_pass(client)

        # Start an assessment
        await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )

        resp = await client.get(
            "/api/assessment/active",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["status"] == "IN_PROGRESS"

    async def test_07_submit_section_unauthorized(self, client: AsyncClient):
        """Test: Submitting to another candidate's assessment returns 400/404."""
        # Register candidate A and start assessment
        token_a, _ = await self._reg_candidate(client)
        await self._screen_and_pass(client)
        start = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"round": "ROUND_2"},
        )
        aid = start.json()["id"]

        # Register candidate B and try to submit to A's assessment
        token_b, _ = await self._reg_candidate(client)
        resp = await client.post(
            "/api/assessment/submit-section",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "assessment_id": aid,
                "section": "CODING",
                "content": {"code": "print('hack')"},
                "time_spent_seconds": 10,
            },
        )
        assert resp.status_code in (400, 404), (
            f"Expected 400/404, got {resp.status_code}: {resp.text}"
        )

    async def test_08_complete_assessment_without_submissions(self, client: AsyncClient):
        """Test: Completing an assessment without any submissions returns 400."""
        token, _ = await self._reg_candidate(client)
        await self._screen_and_pass(client)

        start = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        aid = start.json()["id"]

        # Try to complete without submitting
        resp = await client.post(
            f"/api/assessment/{aid}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        assert "without any submissions" in resp.json()["detail"].lower()

    async def test_09_complete_assessment_twice(self, client: AsyncClient):
        """Test: Completing an already completed assessment returns 400."""
        token, _ = await self._reg_candidate(client)
        await self._screen_and_pass(client)

        start = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        aid = start.json()["id"]

        # Submit first
        await client.post(
            "/api/assessment/submit-section",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "assessment_id": aid,
                "section": "CODING",
                "content": {"code": "print('ok')"},
                "time_spent_seconds": 30,
            },
        )

        # Complete
        r1 = await client.post(
            f"/api/assessment/{aid}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200
        assert r1.json()["status"] == "COMPLETED"

        # Try completing again
        r2 = await client.post(
            f"/api/assessment/{aid}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 400, f"Expected 400, got {r2.status_code}: {r2.text}"
        assert "already completed" in r2.json()["detail"].lower()

    async def test_10_start_round3_after_round2(self, client: AsyncClient):
        """Test: Complete pipeline ROUND_2 -> ROUND_3 assessment."""
        token, _ = await self._reg_candidate(client)
        await self._screen_and_pass(client)

        # Start ROUND_2
        r2 = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        assert r2.status_code == 200
        aid = r2.json()["id"]

        # Submit and complete ROUND_2
        await client.post(
            "/api/assessment/submit-section",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "assessment_id": aid,
                "section": "CODING",
                "content": {"code": "print('round2')"},
                "time_spent_seconds": 30,
            },
        )
        await client.post(
            f"/api/assessment/{aid}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Start ROUND_3
        r3 = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_3"},
        )
        assert r3.status_code == 200, f"Expected 200, got {r3.status_code}: {r3.text}"
        assert r3.json()["round"] == "ROUND_3"
        assert r3.json()["status"] == "IN_PROGRESS"

    async def test_11_submit_section_invalid_section(self, client: AsyncClient):
        """Test: Submitting with an invalid section value returns 422."""
        token, _ = await self._reg_candidate(client)
        await self._screen_and_pass(client)

        start = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        aid = start.json()["id"]

        resp = await client.post(
            "/api/assessment/submit-section",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "assessment_id": aid,
                "section": "INVALID_SECTION",
                "content": {"code": "print('x')"},
                "time_spent_seconds": 10,
            },
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
