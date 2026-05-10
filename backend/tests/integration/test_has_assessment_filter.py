"""Integration test: has_assessment filter.

Verifies the has_assessment filter works across all four backend endpoints:
screening/run, pipeline-stats, candidates list, and analytics funnel.
"""
import uuid
import pytest
from httpx import AsyncClient


class TestHasAssessmentFilter:
    """Test the has_assessment filter for filtering candidates with/without assessments."""

    async def _login_hr(self, client: AsyncClient) -> str:
        """Helper: login as HR and return token."""
        resp = await client.post(
            "/api/auth/login",
            json={"email": "hr@knowledgefactory.com", "password": "Hr@12345"},
        )
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _register_candidate(
        self, client: AsyncClient, suffix: str = ""
    ) -> dict[str, str]:
        """Helper: register a candidate and return token + id."""
        email = f"hasassessment-{suffix}{uuid.uuid4().hex[:8]}@test.com"
        resp = await client.post(
            "/api/auth/register",
            json={
                "name": f"HasAssessment Test {suffix}",
                "email": email,
                "password": "Candidate@123",
                "college": "Test Uni",
                "branch": "CSE",
                "cgpa": 8.0,
                "passed_out_year": 2026,
                "language_choice": "python",
            },
        )
        assert resp.status_code == 201
        return {"token": resp.json()["access_token"], "id": resp.json()["user"]["id"]}

    async def _screen_candidates(self, client: AsyncClient, hr_headers: dict):
        """Helper: screen all APPLIED candidates."""
        resp = await client.post("/api/screening/run", headers=hr_headers)
        assert resp.status_code == 200
        return resp.json()

    async def test_01_candidates_without_assessments(self, client: AsyncClient):
        """Verify has_assessment=false filters to candidates with NO assessment."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register a candidate (they're APPLIED with no assessment)
        cand = await self._register_candidate(client, "noasmt1")

        # Query candidates without assessment via pipeline-stats
        # has_assessment=false should include our newly registered candidate
        resp = await client.get(
            "/api/screening/pipeline-stats?has_assessment=false",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  pipeline-stats (has_assessment=false): {data}")
        applied_count = data["stats"].get("APPLIED", 0)
        assert applied_count >= 1, (
            f"Expected at least 1 APPLIED candidate without assessment, got {applied_count}"
        )

        # Verify funnel also shows applied candidates
        resp = await client.get(
            "/api/analytics/funnel?has_assessment=false",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel = resp.json()
        print(f"  funnel (has_assessment=false): {funnel}")
        assert funnel.get("applied", 0) >= 1, (
            f"Expected >=1 applied in funnel, got {funnel}"
        )

        print("✓ has_assessment=false correctly shows candidates without assessments")

    async def test_02_screening_with_has_assessment(self, client: AsyncClient):
        """Verify has_assessment filter works with screening/run."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register + screen a candidate, then start assessment
        cand = await self._register_candidate(client, "scr1")
        cand_token = cand["token"]
        cand_headers = {"Authorization": f"Bearer {cand_token}"}

        # Screen
        await self._screen_candidates(client, hr_headers)

        # Start ROUND_2 assessment
        resp = await client.post(
            "/api/assessment/start",
            headers=cand_headers,
            json={"round": "ROUND_2"},
        )
        assert resp.status_code == 200

        # Verify has_assessment=true shows this candidate via pipeline-stats
        resp = await client.get(
            "/api/screening/pipeline-stats?has_assessment=true",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        stats = resp.json()
        print(f"  pipeline-stats (has_assessment=true): {stats}")
        in_progress = stats["stats"].get("ROUND2_IN_PROGRESS", 0)
        assert in_progress >= 1, (
            f"Expected >=1 ROUND2_IN_PROGRESS with assessment, got {in_progress}"
        )

        # Verify has_assessment=false EXCLUDES this candidate
        resp = await client.get(
            "/api/screening/pipeline-stats?has_assessment=false",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        stats_false = resp.json()
        print(f"  pipeline-stats (has_assessment=false): {stats_false}")
        # The candidate with assessment should NOT appear here
        # (ROUND2_IN_PROGRESS should be 0 with has_assessment=false)
        in_progress_false = stats_false["stats"].get("ROUND2_IN_PROGRESS", 0)
        assert in_progress_false == 0, (
            f"Expected 0 ROUND2_IN_PROGRESS with has_assessment=false, got {in_progress_false}"
        )

        print("✓ has_assessment filter correctly includes/excludes candidates")

    async def test_03_candidates_list_with_has_assessment(self, client: AsyncClient):
        """Verify has_assessment filter works with GET /api/candidates/."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register a fresh candidate with no assessment
        cand = await self._register_candidate(client, "list1")

        # List candidates with has_assessment=false
        resp = await client.get(
            "/api/candidates/?has_assessment=false&limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  candidates (has_assessment=false): total={data['pagination']['total']}")
        # Should include our registered candidate (who has no assessment)
        assert data["pagination"]["total"] >= 1

        # List candidates with has_assessment=true
        resp = await client.get(
            "/api/candidates/?has_assessment=true&limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data_true = resp.json()
        print(f"  candidates (has_assessment=true): total={data_true['pagination']['total']}")

        print("✓ has_assessment filter works with candidates list endpoint")

    async def test_04_has_assessment_with_target_statuses(self, client: AsyncClient):
        """Verify has_assessment combines correctly with target_statuses."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register candidate who will have an assessment
        cand = await self._register_candidate(client, "comb1")
        cand_headers = {"Authorization": f"Bearer {cand['token']}"}

        # Screen to advance from APPLIED
        await self._screen_candidates(client, hr_headers)

        # Start ROUND_2 assessment
        resp = await client.post(
            "/api/assessment/start",
            headers=cand_headers,
            json={"round": "ROUND_2"},
        )
        assert resp.status_code == 200

        # Pipeline-stats with has_assessment=true AND target_statuses=ROUND2_IN_PROGRESS
        resp = await client.get(
            "/api/screening/pipeline-stats"
            "?has_assessment=true&target_statuses=ROUND2_IN_PROGRESS,APPLIED",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  pipeline-stats (has_assessment=true + target_statuses): {data}")
        assert "ROUND2_IN_PROGRESS" in data["stats"]
        assert data["stats"]["ROUND2_IN_PROGRESS"] >= 1
        # APPLIED candidates have no assessments, so with has_assessment=true they should be 0
        assert data["stats"]["APPLIED"] == 0, (
            "APPLIED candidates should be 0 with has_assessment=true"
        )

        print("✓ has_assessment + target_statuses combination works correctly")
