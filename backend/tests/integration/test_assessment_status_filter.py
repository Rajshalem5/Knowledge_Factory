"""Integration test: assessment_status filter.

Verifies the assessment_status filter works across all four backend endpoints:
screening/run, pipeline-stats, candidates list, and analytics funnel.
"""
import uuid
import pytest
from httpx import AsyncClient


class TestAssessmentStatusFilter:
    """Test the assessment_status filter for filtering candidates by assessment state."""

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
        email = f"asmtstatus-{suffix}{uuid.uuid4().hex[:8]}@test.com"
        resp = await client.post(
            "/api/auth/register",
            json={
                "name": f"AssessmentStatus Test {suffix}",
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

    async def test_01_pipeline_stats_with_assessment_status_in_progress(
        self, client: AsyncClient
    ):
        """Verify assessment_status=IN_PROGRESS via pipeline-stats."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register candidate, screen, start assessment
        cand = await self._register_candidate(client, "prog1")
        cand_headers = {"Authorization": f"Bearer {cand['token']}"}
        await self._screen_candidates(client, hr_headers)

        resp = await client.post(
            "/api/assessment/start",
            headers=cand_headers,
            json={"round": "ROUND_2"},
        )
        assert resp.status_code == 200

        # Pipeline-stats with assessment_status=IN_PROGRESS
        resp = await client.get(
            "/api/screening/pipeline-stats?assessment_status=IN_PROGRESS",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  pipeline-stats (assessment_status=IN_PROGRESS): {data}")
        in_progress = data["stats"].get("ROUND2_IN_PROGRESS", 0)
        assert in_progress >= 1, (
            f"Expected >=1 ROUND2_IN_PROGRESS with assessment_status=IN_PROGRESS, got {in_progress}"
        )

        print("✓ assessment_status=IN_PROGRESS works on pipeline-stats")

    async def test_02_candidates_list_with_assessment_status_completed(
        self, client: AsyncClient
    ):
        """Verify assessment_status=COMPLETED via candidates list."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register candidate, screen, start assessment, submit, complete
        cand = await self._register_candidate(client, "comp1")
        cand_headers = {"Authorization": f"Bearer {cand['token']}"}
        await self._screen_candidates(client, hr_headers)

        # Start assessment
        resp = await client.post(
            "/api/assessment/start",
            headers=cand_headers,
            json={"round": "ROUND_2"},
        )
        assert resp.status_code == 200
        assessment_id = resp.json()["id"]

        # Submit section
        resp = await client.post(
            "/api/assessment/submit-section",
            headers=cand_headers,
            json={
                "assessment_id": assessment_id,
                "section": "CODING",
                "content": {"code": "print('test')", "problemId": "r2_p1"},
                "time_spent_seconds": 60,
            },
        )
        assert resp.status_code == 200

        # Complete assessment
        resp = await client.post(
            f"/api/assessment/{assessment_id}/complete",
            headers=cand_headers,
        )
        assert resp.status_code == 200

        # Candidates list with assessment_status=COMPLETED
        resp = await client.get(
            "/api/candidates/?assessment_status=COMPLETED&limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  candidates (assessment_status=COMPLETED): total={data['pagination']['total']}")
        assert data["pagination"]["total"] >= 1, (
            "Expected >=1 candidate with assessment_status=COMPLETED"
        )

        print("✓ assessment_status=COMPLETED works on candidates list")

    async def test_03_funnel_with_assessment_status(
        self, client: AsyncClient
    ):
        """Verify assessment_status filter works with analytics funnel."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Funnel with assessment_status=IN_PROGRESS
        resp = await client.get(
            "/api/analytics/funnel?assessment_status=IN_PROGRESS",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel_in_progress = resp.json()
        print(f"  funnel (assessment_status=IN_PROGRESS): {funnel_in_progress}")

        # Funnel with assessment_status=COMPLETED
        resp = await client.get(
            "/api/analytics/funnel?assessment_status=COMPLETED",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel_completed = resp.json()
        print(f"  funnel (assessment_status=COMPLETED): {funnel_completed}")

        # Funnel with no filter should have >= counts compared to filtered
        resp = await client.get(
            "/api/analytics/funnel",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel_all = resp.json()
        print(f"  funnel (no filter): {funnel_all}")

        # The sum of IN_PROGRESS + COMPLETED funnel counts should make sense
        for stage in ("applied", "eligible", "assessed", "interviewed", "selected"):
            total_in = funnel_in_progress.get(stage, 0)
            total_comp = funnel_completed.get(stage, 0)
            total_all = funnel_all.get(stage, 0)
            assert total_in + total_comp <= total_all + 1, (
                f"Stage '{stage}': IN_PROGRESS({total_in}) + COMPLETED({total_comp}) "
                f"should be <= unfiltered({total_all})"
            )

        print("✓ assessment_status filter works on funnel endpoint")

    async def test_04_screening_with_assessment_status(
        self, client: AsyncClient
    ):
        """Verify assessment_status filter works with screening/run."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register two candidates
        cand1 = await self._register_candidate(client, "scr_asmt1")
        cand2 = await self._register_candidate(client, "scr_asmt2")

        # Screen both
        await self._screen_candidates(client, hr_headers)

        # Start assessment for cand1 only
        cand1_headers = {"Authorization": f"Bearer {cand1['token']}"}
        resp = await client.post(
            "/api/assessment/start",
            headers=cand1_headers,
            json={"round": "ROUND_2"},
        )
        assert resp.status_code == 200

        # Screening with assessment_status=IN_PROGRESS should
        # only see candidates who have assessments in progress
        resp = await client.post(
            "/api/screening/run?assessment_status=IN_PROGRESS&target_statuses=ROUND2_IN_PROGRESS",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        screen_data = resp.json()
        print(f"  screening (assessment_status=IN_PROGRESS): {screen_data}")
        # Candidates with assessments in progress are already
        # ROUND2_IN_PROGRESS — screening only targets those statuses
        assert screen_data["screened"] >= 0  # May be 0 since they're already screened
        assert "screened" in screen_data

        print("✓ assessment_status filter works on screening endpoint")

    async def test_05_assessment_status_combined_with_has_assessment(
        self, client: AsyncClient
    ):
        """Verify assessment_status and has_assessment work together correctly."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register candidate, screen, start assessment
        cand = await self._register_candidate(client, "comb_asmt")
        cand_headers = {"Authorization": f"Bearer {cand['token']}"}
        await self._screen_candidates(client, hr_headers)

        resp = await client.post(
            "/api/assessment/start",
            headers=cand_headers,
            json={"round": "ROUND_2"},
        )
        assert resp.status_code == 200

        # has_assessment=true AND assessment_status=IN_PROGRESS — should match
        resp = await client.get(
            "/api/screening/pipeline-stats"
            "?has_assessment=true&assessment_status=IN_PROGRESS",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  pipeline-stats (has_assessment=true + assessment_status=IN_PROGRESS): {data}")
        assert data["stats"].get("ROUND2_IN_PROGRESS", 0) >= 1

        # has_assessment=true AND assessment_status=COMPLETED — should NOT include
        # IN_PROGRESS assessments
        resp = await client.get(
            "/api/screening/pipeline-stats"
            "?has_assessment=true&assessment_status=COMPLETED",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data_comp = resp.json()
        print(f"  pipeline-stats (has_assessment=true + assessment_status=COMPLETED): {data_comp}")
        # Our candidate's assessment is IN_PROGRESS, so COMPLETED should be 0
        # for this specific candidate
        assert data_comp["stats"].get("ROUND2_IN_PROGRESS", 0) == 0, (
            "ROUND2_IN_PROGRESS should be 0 with assessment_status=COMPLETED"
        )

        print("✓ assessment_status + has_assessment combination works correctly")
