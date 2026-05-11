"""Integration tests for screening run endpoint — edge cases, re-screening, and filter combinations.

Tests POST /api/screening/run with various filter combinations
and candidate status transitions. All tests register their own candidates
to avoid test ordering dependencies on seed data.
"""
import uuid
import pytest
from httpx import AsyncClient


class TestScreeningRun:
    """Test the screening run endpoint — fully self-contained candidates."""

    async def _login_hr(self, client: AsyncClient) -> dict:
        resp = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert resp.status_code == 200
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def _login_admin(self, client: AsyncClient) -> dict:
        resp = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert resp.status_code == 200
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def _register_candidate(self, client: AsyncClient, **overrides) -> dict:
        """Register a candidate and return (token, candidate_id)."""
        suffix = uuid.uuid4().hex[:8]
        payload = {
            "name": overrides.get("name", f"Screening Test {suffix}"),
            "email": overrides.get("email", f"screen-{suffix}@test.com"),
            "password": "Candidate@123",
            "college": overrides.get("college", "Test Uni"),
            "branch": overrides.get("branch", "CSE"),
            "cgpa": overrides.get("cgpa", 8.5),
            "passed_out_year": overrides.get("passed_out_year", 2026),
            "language_choice": overrides.get("language_choice", "python"),
        }
        resp = await client.post("/api/auth/register", json=payload)
        assert resp.status_code == 201, resp.text
        token = resp.json()["access_token"]
        c_headers = {"Authorization": f"Bearer {token}"}
        me = await client.get("/api/candidates/me", headers=c_headers)
        assert me.status_code == 200
        return {"token": token, "id": me.json()["id"]}

    async def test_01_screening_moves_applied_to_passed_or_rejected(self, client: AsyncClient):
        """Default screening targets APPLIED candidates and moves them based on eligibility."""
        hr_headers = await self._login_hr(client)

        # Register 3 candidates with different profiles
        passing = await self._register_candidate(client, name="Passing CSE", branch="CSE", cgpa=8.5)
        low_cgpa = await self._register_candidate(client, name="Low CGPA", branch="CSE", cgpa=5.0)
        wrong_branch = await self._register_candidate(client, name="Wrong Branch", branch="MECH", cgpa=7.5)

        # Run screening
        resp = await client.post("/api/screening/run", headers=hr_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["screened"] == 3
        assert data["passed"] >= 1  # At least the passing candidate
        assert data["rejected"] >= 1  # At least low CGPA or wrong branch
        assert "min_cgpa" in data
        assert "allowed_branches" in data

        # Verify statuses
        for cand, expected in [(passing, "ROUND1_PASSED"), (low_cgpa, "ROUND1_REJECTED"), (wrong_branch, "ROUND1_REJECTED")]:
            resp = await client.get(
                f"/api/candidates/{cand['id']}",
                headers=hr_headers,
            )
            assert resp.status_code == 200, f"Failed to get {cand['id']}"
            status = resp.json()["status"]
            assert status == expected, f"Expected {expected}, got {status} for {resp.json()['name']}"

    async def test_02_screening_with_branch_filter(self, client: AsyncClient):
        """Branch filter narrows screening scope."""
        hr_headers = await self._login_hr(client)

        await self._register_candidate(client, branch="CSE", cgpa=8.5)
        await self._register_candidate(client, branch="ECE", cgpa=8.0)
        await self._register_candidate(client, branch="MECH", cgpa=7.5)

        resp = await client.post(
            "/api/screening/run?branch=CSE",
            headers=hr_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["screened"] == 1  # Only CSE candidate
        assert data["passed"] == 1     # CSE 8.5 satisfies criteria

    async def test_03_screening_with_cgpa_override(self, client: AsyncClient):
        """min_cgpa_override overrides the cycle's default min_cgpa."""
        hr_headers = await self._login_hr(client)

        await self._register_candidate(client, cgpa=8.5)
        await self._register_candidate(client, cgpa=6.5)

        resp = await client.post(
            "/api/screening/run?min_cgpa_override=8.0",
            headers=hr_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["screened"] == 2
        assert data["passed"] == 1  # Only 8.5 passes with 8.0 minimum

    async def test_04_screening_with_name_filter(self, client: AsyncClient):
        """Name filter narrows screening to matching candidates."""
        hr_headers = await self._login_hr(client)

        await self._register_candidate(client, name="Alpha Coder", branch="CSE", cgpa=8.5)
        await self._register_candidate(client, name="Beta Coder", branch="CSE", cgpa=7.5)

        resp = await client.post(
            "/api/screening/run?name=Beta",
            headers=hr_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["screened"] == 1  # Only "Beta Coder"
        assert data["passed"] == 1

    async def test_05_screening_with_college_filter(self, client: AsyncClient):
        """College filter narrows scope."""
        hr_headers = await self._login_hr(client)

        await self._register_candidate(client, college="MIT")
        await self._register_candidate(client, college="Stanford")

        resp = await client.post(
            "/api/screening/run?college=MIT",
            headers=hr_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["screened"] == 1  # Only MIT candidate

    async def test_06_re_screening_newly_registered_only(self, client: AsyncClient):
        """After initial screening, running again only sees newly APPLIED candidates."""
        hr_headers = await self._login_hr(client)

        # Register one batch and screen
        await self._register_candidate(client, name="Batch1", branch="CSE", cgpa=8.5)
        resp = await client.post("/api/screening/run", headers=hr_headers)
        assert resp.status_code == 200
        assert resp.json()["screened"] == 1

        # Register another candidate — not yet screened
        await self._register_candidate(client, name="Batch2", branch="CSE", cgpa=7.5)

        # Second screening only sees the new APPLIED candidate
        resp = await client.post("/api/screening/run", headers=hr_headers)
        assert resp.status_code == 200
        data2 = resp.json()
        assert data2["screened"] == 1  # Only the newly registered
        assert data2["passed"] == 1

    async def test_07_re_screening_existing_statuses(self, client: AsyncClient):
        """target_statuses allows re-screening candidates in specific statuses."""
        hr_headers = await self._login_hr(client)

        # Register and screen
        await self._register_candidate(client, branch="CSE", cgpa=8.5)
        await client.post("/api/screening/run", headers=hr_headers)

        # Re-screen only ROUND1_PASSED candidates
        resp = await client.post(
            "/api/screening/run?target_statuses=ROUND1_PASSED",
            headers=hr_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["screened"] >= 1
        assert data["passed"] >= 1

    async def test_08_invalid_target_status(self, client: AsyncClient):
        """Invalid target_status returns 422."""
        hr_headers = await self._login_hr(client)

        resp = await client.post(
            "/api/screening/run?target_statuses=INVALID_STATUS",
            headers=hr_headers,
        )
        assert resp.status_code == 422, resp.text

    async def test_09_screening_requires_hr_role(self, client: AsyncClient):
        """Candidate role cannot run screening."""
        cand = await self._register_candidate(client, branch="CSE", cgpa=8.5)
        c_headers = {"Authorization": f"Bearer {cand['token']}"}

        resp = await client.post("/api/screening/run", headers=c_headers)
        assert resp.status_code == 403, resp.text

    async def test_10_screening_unauthenticated(self, client: AsyncClient):
        """Unauthenticated request returns 401."""
        resp = await client.post("/api/screening/run")
        assert resp.status_code == 401, resp.text
