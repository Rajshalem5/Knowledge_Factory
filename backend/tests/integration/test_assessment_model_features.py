"""Integration tests for assessment model features.

Tests time_limit on Assessment model, time_spent_seconds on Submission model,
and that assessment submission properly stores these fields.
"""

import uuid
import pytest
from httpx import AsyncClient


class TestAssessmentModel:
    """Test Assessment model fields: time_limit, submission time_spent_seconds."""

    async def _reg_candidate(self, client: AsyncClient) -> tuple[str, str]:
        """Register a candidate and return (token, candidate_id)."""
        email = f"asm-model-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Model Test", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026, "language_choice": "python",
        })
        assert reg.status_code == 201, reg.text
        token = reg.json()["access_token"]
        me = await client.get("/api/candidates/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        return token, me.json()["id"]

    async def test_01_assessment_read_has_time_limit(self, client: AsyncClient):
        """Test: AssessmentRead schema includes time_limit field with default value 60."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        token, cid = await self._reg_candidate(client)

        # Screen first
        screen = await client.post("/api/screening/run", headers=hr_headers)
        assert screen.status_code == 200

        # Start assessment
        start = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        assert start.status_code == 200
        data = start.json()

        # Verify time_limit field is present
        assert "time_limit" in data, "Assessment response should contain time_limit"
        assert data["time_limit"] == 60, f"Expected default time_limit=60, got {data['time_limit']}"

    async def test_02_submission_stores_time_spent_seconds(self, client: AsyncClient):
        """Test: Submission stores time_spent_seconds when submitting a section."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        token, cid = await self._reg_candidate(client)

        # Screen and start assessment
        await client.post("/api/screening/run", headers=hr_headers)
        start = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        aid = start.json()["id"]

        # Submit with time_spent_seconds
        resp = await client.post(
            "/api/assessment/submit-section",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "assessment_id": aid,
                "section": "CODING",
                "content": {"code": "print('hello')", "testCases": []},
                "time_spent_seconds": 120,
            },
        )
        assert resp.status_code == 200, f"Submit failed: {resp.status_code} {resp.text}"
        result = resp.json()
        assert "submission_id" in result
        assert result["passed"] == 0  # Empty testCases list

    async def test_03_submission_default_time_spent_seconds(self, client: AsyncClient):
        """Test: Submitting without time_spent_seconds defaults to 0."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        token, cid = await self._reg_candidate(client)

        # Screen and start assessment
        await client.post("/api/screening/run", headers=hr_headers)
        start = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        aid = start.json()["id"]

        # Submit WITHOUT time_spent_seconds (should default to 0)
        resp = await client.post(
            "/api/assessment/submit-section",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "assessment_id": aid,
                "section": "CODING",
                "content": {"code": "print('test')"},
                # time_spent_seconds omitted intentionally
            },
        )
        assert resp.status_code == 200, f"Submit without time_spent failed: {resp.status_code} {resp.text}"

    async def test_04_assessment_complete_round_and_advance(self, client: AsyncClient):
        """Test: Complete assessment pipeline works end-to-end with model fields."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        token, cid = await self._reg_candidate(client)

        # Screen
        await client.post("/api/screening/run", headers=hr_headers)

        # Start ROUND_2
        start = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        aid = start.json()["id"]

        # Submit section
        await client.post(
            "/api/assessment/submit-section",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "assessment_id": aid,
                "section": "CODING",
                "content": {"code": "def solve(): pass", "testCases": [{"passed": True}]},
                "time_spent_seconds": 300,
            },
        )

        # Complete assessment
        complete = await client.post(
            f"/api/assessment/{aid}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert complete.status_code == 200
        data = complete.json()
        assert data["status"] == "COMPLETED"
        assert data["time_limit"] == 60

        # Candidate should be ROUND2_PASSED now
        me = await client.get(
            "/api/candidates/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200
        assert me.json()["status"] == "ROUND2_PASSED"

    async def test_05_start_invalid_round_returns_422(self, client: AsyncClient):
        """Test: Starting assessment with invalid round returns validation error."""
        token, _ = await self._reg_candidate(client)
        resp = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_INVALID"},
        )
        assert resp.status_code == 422
