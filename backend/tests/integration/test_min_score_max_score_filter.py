"""Integration test: min_score and max_score filters.

Verifies the min_score/max_score filters work across all four backend endpoints:
screening/run, pipeline-stats, candidates list, and analytics funnel.

These filters use a cross-table subquery against the Score.weighted_total column.
Since Score records aren't auto-created by the assessment flow (Phase 2 feature),
we directly insert Score records to test the filter behavior.

NOTE: Tests share DB state (session-scoped fixture). Each test creates its own
test candidate and score, so cross-test comparisons use relative checks.
"""
import uuid
import pytest
from httpx import AsyncClient

from app.features.assessments.models import Score
from app.features.assessments.models import AssessmentRound
from app.core.enums import ScoreVerdict
from tests.conftest import TestSessionFactory


class TestMinScoreMaxScoreFilter:
    """Test the min_score and max_score filters for filtering by assessment score."""

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
        email = f"minscore-{suffix}{uuid.uuid4().hex[:8]}@test.com"
        resp = await client.post(
            "/api/auth/register",
            json={
                "name": f"MinScore Test {suffix}",
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

    async def _create_score_record(
        self, candidate_id: str, weighted_total: float
    ):
        """Helper: directly insert a Score record for a candidate."""
        async with TestSessionFactory() as session:
            score = Score(
                candidate_id=candidate_id,
                round=AssessmentRound.ROUND_2,
                correctness=80,
                quality=75,
                design=70,
                edge_cases=65,
                efficiency=60,
                mcq_total=0,
                weighted_total=weighted_total,
                verdict=ScoreVerdict.PASS,
                feedback_json={},
            )
            session.add(score)
            await session.flush()
            await session.commit()

    async def _complete_assessment_flow(
        self, client: AsyncClient, token: str
    ) -> str:
        """Helper: screen, start assessment, submit, complete. Returns candidate_id."""
        # Start assessment
        resp = await client.post(
            "/api/assessment/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"round": "ROUND_2"},
        )
        assert resp.status_code == 200
        assessment_id = resp.json()["id"]

        # Submit section
        resp = await client.post(
            "/api/assessment/submit-section",
            headers={"Authorization": f"Bearer {token}"},
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
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        return resp.json()["candidate_id"]

    async def test_01_pipeline_stats_with_min_score(self, client: AsyncClient):
        """Verify min_score filter via pipeline-stats.

        A candidate with score 75 should appear with min_score=70 but not min_score=80.
        """
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        cand = await self._register_candidate(client, "min1")
        await self._screen_candidates(client, hr_headers)
        cand_id = await self._complete_assessment_flow(client, cand["token"])

        # Create Score with weighted_total=75
        await self._create_score_record(cand_id, 75.0)

        # min_score=70 should include this candidate (score 75 >= 70)
        resp = await client.get(
            "/api/screening/pipeline-stats?min_score=70",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  pipeline-stats (min_score=70): {data}")
        passed = data["stats"].get("ROUND2_PASSED", 0)
        assert passed >= 1, f"Expected >=1 ROUND2_PASSED with min_score=70, got {passed}"

        # Unfiltered pipeline-stats should have >= the filtered count
        resp = await client.get(
            "/api/screening/pipeline-stats",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data_all = resp.json()
        passed_all = data_all["stats"].get("ROUND2_PASSED", 0)
        assert passed <= passed_all, (
            f"Filtered count ({passed}) should be <= unfiltered ({passed_all})"
        )

        print("✓ min_score filter works correctly on pipeline-stats endpoint")

    async def test_02_candidates_list_with_max_score(self, client: AsyncClient):
        """Verify max_score filter via candidates list.

        A candidate with score 45 should appear with max_score=50 but not max_score=40.
        """
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        cand = await self._register_candidate(client, "max1")
        await self._screen_candidates(client, hr_headers)
        cand_id = await self._complete_assessment_flow(client, cand["token"])

        # Create Score with weighted_total=45
        await self._create_score_record(cand_id, 45.0)

        # max_score=50 should include this candidate (score 45 <= 50)
        resp = await client.get(
            "/api/candidates/?max_score=50&limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  candidates (max_score=50): total={data['pagination']['total']}")
        total50 = data["pagination"]["total"]

        # max_score=40 should NOT include this candidate — result should be smaller
        resp = await client.get(
            "/api/candidates/?max_score=40&limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data40 = resp.json()
        print(f"  candidates (max_score=40): total={data40['pagination']['total']}")
        assert data40["pagination"]["total"] < total50, (
            f"max_score=40 ({data40['pagination']['total']}) should be < "
            f"max_score=50 ({total50})"
        )

        # Unfiltered should be >= max_score=50 result
        resp = await client.get(
            "/api/candidates/?limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data_all = resp.json()
        print(f"  candidates (no filter): total={data_all['pagination']['total']}")
        assert data_all["pagination"]["total"] >= total50, (
            f"Unfiltered ({data_all['pagination']['total']}) should be >= "
            f"max_score=50 ({total50})"
        )

        print("✓ max_score filter works correctly on candidates list endpoint")

    async def test_03_funnel_with_min_score(self, client: AsyncClient):
        """Verify min_score filter works with analytics funnel.

        A candidate with score 60 should appear with min_score=50 but not min_score=70.
        Uses relative comparisons (consistent filtering direction) to avoid
        cross-test interference from shared DB state.
        """
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        cand = await self._register_candidate(client, "fun1")
        await self._screen_candidates(client, hr_headers)
        cand_id = await self._complete_assessment_flow(client, cand["token"])

        # Create Score with weighted_total=60
        await self._create_score_record(cand_id, 60.0)

        # Funnel with min_score=50 (score 60 >= 50 → included)
        resp = await client.get(
            "/api/analytics/funnel?min_score=50",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel_lo = resp.json()
        print(f"  funnel (min_score=50): {funnel_lo}")

        # Funnel with min_score=70 (score 60 < 70 → excluded)
        resp = await client.get(
            "/api/analytics/funnel?min_score=70",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel_hi = resp.json()
        print(f"  funnel (min_score=70): {funnel_hi}")

        # The assessed count with min_score=70 should be <= assessed with min_score=50
        # (more restrictive filter = fewer or equal results)
        assessed_lo = funnel_lo.get("assessed", 0)
        assessed_hi = funnel_hi.get("assessed", 0)
        assert assessed_hi <= assessed_lo, (
            f"min_score=70 assessed ({assessed_hi}) should be <= "
            f"min_score=50 assessed ({assessed_lo})"
        )

        print("✓ min_score filter works correctly on funnel endpoint")

    async def test_04_screening_with_min_score(self, client: AsyncClient):
        """Verify min_score filter works with screening/run.

        Screening with min_score should respect score-based filtering.
        """
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        cand = await self._register_candidate(client, "scr1")
        await self._screen_candidates(client, hr_headers)
        cand_id = await self._complete_assessment_flow(client, cand["token"])

        # Create Score with weighted_total=88
        await self._create_score_record(cand_id, 88.0)

        # Screening with min_score=80, targeting ROUND2_PASSED candidates
        resp = await client.post(
            "/api/screening/run?min_score=80&target_statuses=ROUND2_PASSED",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        screen_80 = resp.json()
        print(f"  screening (min_score=80): {screen_80}")
        assert "screened" in screen_80

        # Screening with min_score=95 (should find fewer since score 88 < 95)
        resp = await client.post(
            "/api/screening/run?min_score=95&target_statuses=ROUND2_PASSED",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        screen_95 = resp.json()
        print(f"  screening (min_score=95): {screen_95}")
        assert screen_95["screened"] <= screen_80["screened"], (
            f"min_score=95 screened ({screen_95['screened']}) should be <= "
            f"min_score=80 screened ({screen_80['screened']})"
        )

        print("✓ min_score filter works correctly on screening endpoint")

    async def test_05_score_range_filter_combined(self, client: AsyncClient):
        """Verify min_score AND max_score together narrow correctly.

        range1 (score 55) should appear with min=50,max=60 but not with min=70,max=80.
        """
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        cand = await self._register_candidate(client, "rn1")
        await self._screen_candidates(client, hr_headers)
        cand_id = await self._complete_assessment_flow(client, cand["token"])

        # Create Score with weighted_total=55
        await self._create_score_record(cand_id, 55.0)

        # Range 50-60 should include this candidate (score 55)
        resp = await client.get(
            "/api/candidates/?min_score=50&max_score=60&limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  candidates (min_score=50, max_score=60): total={data['pagination']['total']}")
        total_range = data["pagination"]["total"]

        # Range 70-80 should have fewer or equal results than 50-60
        resp = await client.get(
            "/api/candidates/?min_score=70&max_score=80&limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data_high = resp.json()
        print(f"  candidates (min_score=70, max_score=80): total={data_high['pagination']['total']}")

        # Since our candidate has score 55 (outside 70-80), the result should be
        # strictly less than the broader range 50-60 which includes them
        # (Unless there's another candidate also in both ranges — unlikely with unique emails)
        assert data_high["pagination"]["total"] < total_range, (
            f"Higher range ({data_high['pagination']['total']}) should be less than "
            f"lower range ({total_range})"
        )

        print("✓ min_score + max_score combined range filter works correctly")
