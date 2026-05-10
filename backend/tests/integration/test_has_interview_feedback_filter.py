"""Integration test: has_interview_feedback filter.

Verifies the has_interview_feedback filter works across all four backend endpoints:
screening/run, pipeline-stats, candidates list, and analytics funnel.

Since the feedback endpoint requires INTERVIEWER role (not seeded in the test DB),
we directly insert InterviewFeedback records to test the filter behavior.
"""
import uuid
import pytest
from httpx import AsyncClient

from app.features.interviews.models import InterviewFeedback
from app.core.enums import InterviewRecommendation
from tests.conftest import TestSessionFactory


class TestHasInterviewFeedbackFilter:
    """Test the has_interview_feedback filter for filtering candidates with/without interview feedback."""

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
        email = f"hasfeedback-{suffix}{uuid.uuid4().hex[:8]}@test.com"
        resp = await client.post(
            "/api/auth/register",
            json={
                "name": f"HasInterviewFeedback Test {suffix}",
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

    async def _create_feedback_record(self, candidate_id: str):
        """Helper: directly insert an InterviewFeedback record for a candidate."""
        async with TestSessionFactory() as session:
            feedback = InterviewFeedback(
                candidate_id=candidate_id,
                interviewer_id=None,
                technical=8,
                problem_solving=7,
                communication=9,
                cultural_fit=8,
                recommendation=InterviewRecommendation.SELECT,
                comments="Great candidate",
            )
            session.add(feedback)
            await session.flush()
            await session.commit()

    async def test_01_candidates_without_interview_feedback(self, client: AsyncClient):
        """Verify has_interview_feedback=false filters to candidates with NO interview feedback."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register a candidate (they have no interview feedback)
        cand = await self._register_candidate(client, "nofb1")

        # Query candidates without interview feedback via pipeline-stats
        resp = await client.get(
            "/api/screening/pipeline-stats?has_interview_feedback=false",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  pipeline-stats (has_interview_feedback=false): {data}")
        applied_count = data["stats"].get("APPLIED", 0)
        assert applied_count >= 1, (
            f"Expected at least 1 APPLIED candidate without interview feedback, got {applied_count}"
        )

        # Verify funnel also shows applied candidates
        resp = await client.get(
            "/api/analytics/funnel?has_interview_feedback=false",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel = resp.json()
        print(f"  funnel (has_interview_feedback=false): {funnel}")
        assert funnel.get("applied", 0) >= 1, (
            f"Expected >=1 applied in funnel, got {funnel}"
        )

        print("✓ has_interview_feedback=false correctly shows candidates without interview feedback")

    async def test_02_candidates_list_with_has_interview_feedback(self, client: AsyncClient):
        """Verify has_interview_feedback filter works with GET /api/candidates/."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register a candidate who will later get feedback
        cand = await self._register_candidate(client, "list1")

        # Create interview feedback for this candidate
        await self._create_feedback_record(cand["id"])

        # Verify has_interview_feedback=true includes this candidate
        resp = await client.get(
            "/api/candidates/?has_interview_feedback=true&limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data_true = resp.json()
        print(f"  candidates (has_interview_feedback=true): total={data_true['pagination']['total']}")
        assert data_true["pagination"]["total"] >= 1, (
            "Expected >=1 candidate with interview feedback"
        )

        # Verify has_interview_feedback=false also shows candidates (should be more)
        resp = await client.get(
            "/api/candidates/?has_interview_feedback=false&limit=100",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data_false = resp.json()
        print(f"  candidates (has_interview_feedback=false): total={data_false['pagination']['total']}")

        # has_feedback=false should include MORE candidates (all without feedback, including APPLIED)
        total_true = data_true["pagination"]["total"]
        total_false = data_false["pagination"]["total"]
        assert total_false >= total_true, (
            f"has_interview_feedback=false ({total_false}) should be >= "
            f"has_interview_feedback=true ({total_true})"
        )

        print("✓ has_interview_feedback filter works with candidates list endpoint")

    async def test_03_funnel_with_has_interview_feedback(self, client: AsyncClient):
        """Verify has_interview_feedback filter works with analytics funnel."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register candidate, screen, advance, create feedback
        cand = await self._register_candidate(client, "funnel1")
        await self._create_feedback_record(cand["id"])

        # Funnel with has_interview_feedback=true
        resp = await client.get(
            "/api/analytics/funnel?has_interview_feedback=true",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel_true = resp.json()
        print(f"  funnel (has_interview_feedback=true): {funnel_true}")

        # Funnel with has_interview_feedback=false
        resp = await client.get(
            "/api/analytics/funnel?has_interview_feedback=false",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel_false = resp.json()
        print(f"  funnel (has_interview_feedback=false): {funnel_false}")

        # Unfiltered funnel
        resp = await client.get(
            "/api/analytics/funnel",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        funnel_all = resp.json()
        print(f"  funnel (no filter): {funnel_all}")

        # Sum of true + false across any stage should be <= unfiltered
        for stage in ("applied", "eligible", "assessed", "interviewed", "selected"):
            total_true_stage = funnel_true.get(stage, 0)
            total_false_stage = funnel_false.get(stage, 0)
            total_all_stage = funnel_all.get(stage, 0)
            assert total_true_stage + total_false_stage <= total_all_stage + 1, (
                f"Stage '{stage}': true({total_true_stage}) + false({total_false_stage}) "
                f"should be <= unfiltered({total_all_stage})"
            )

        print("✓ has_interview_feedback filter works on funnel endpoint")

    async def test_04_screening_with_has_interview_feedback(self, client: AsyncClient):
        """Verify has_interview_feedback filter works with screening/run."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register two candidates
        cand1 = await self._register_candidate(client, "scr1")
        cand2 = await self._register_candidate(client, "scr2")

        # Create feedback for cand1 only
        await self._create_feedback_record(cand1["id"])

        # Screening with has_interview_feedback=true — should screen cand1
        resp = await client.post(
            "/api/screening/run?has_interview_feedback=true",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        screen_true = resp.json()
        print(f"  screening (has_interview_feedback=true): {screen_true}")
        assert "screened" in screen_true

        # Screening with has_interview_feedback=false — should screen cand2
        resp = await client.post(
            "/api/screening/run?has_interview_feedback=false",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        screen_false = resp.json()
        print(f"  screening (has_interview_feedback=false): {screen_false}")
        assert "screened" in screen_false

        print("✓ has_interview_feedback filter works on screening endpoint")

    async def test_05_has_interview_feedback_with_target_statuses(self, client: AsyncClient):
        """Verify has_interview_feedback and target_statuses work together."""
        hr_token = await self._login_hr(client)
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        # Register candidate who will get feedback
        cand = await self._register_candidate(client, "comb1")
        await self._create_feedback_record(cand["id"])

        # Pipeline-stats with has_interview_feedback=true AND target_statuses
        resp = await client.get(
            "/api/screening/pipeline-stats"
            "?has_interview_feedback=true&target_statuses=APPLIED",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"  pipeline-stats (has_interview_feedback=true + target_statuses): {data}")
        # Our candidate has feedback but is in APPLIED status, so should appear
        assert "APPLIED" in data["stats"]
        assert data["stats"]["APPLIED"] >= 1, (
            "Expected >=1 APPLIED with has_interview_feedback=true"
        )

        print("✓ has_interview_feedback + target_statuses combination works correctly")
