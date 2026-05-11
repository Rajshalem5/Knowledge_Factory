"""Integration tests for interview feedback flow.

Tests submit and get feedback endpoints, interviewer relationship,
and the candidate status transition (INTERVIEW_SCHEDULED -> INTERVIEW_COMPLETED).
"""

import uuid
import pytest
from httpx import AsyncClient


class TestInterviewFeedback:
    """Test interview feedback CRUD and status transitions."""

    async def _reg_candidate(self, client: AsyncClient) -> tuple[str, str]:
        """Register a candidate and return (token, candidate_id)."""
        email = f"ift-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Interview Test", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026, "language_choice": "python",
        })
        assert reg.status_code == 201, reg.text
        token = reg.json()["access_token"]
        me = await client.get("/api/candidates/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        return token, me.json()["id"]

    async def _move_to_interview_scheduled(
        self, client: AsyncClient, candidate_id: str, admin_headers: dict
    ) -> None:
        """Move candidate through pipeline step by step to INTERVIEW_SCHEDULED."""
        # Screening already runs at setup — candidates are moved to ROUND1_PASSED / REJECTED
        # For our candidate (cgpa 8.5, CSE branch), they should be ROUND1_PASSED
        # after screening. We advance step by step through FSM-valid transitions.

        transitions = [
            "ROUND2_IN_PROGRESS",  # ROUND1_PASSED -> ROUND2_IN_PROGRESS
            "ROUND2_PASSED",       # ROUND2_IN_PROGRESS -> ROUND2_PASSED
            "ROUND3_IN_PROGRESS",  # ROUND2_PASSED -> ROUND3_IN_PROGRESS
            "ROUND3_PASSED",       # ROUND3_IN_PROGRESS -> ROUND3_PASSED
            "INTERVIEW_SCHEDULED", # ROUND3_PASSED -> INTERVIEW_SCHEDULED
        ]
        for target in transitions:
            resp = await client.patch(
                f"/api/candidates/{candidate_id}/status",
                headers=admin_headers,
                json={"status": target},
            )
            assert resp.status_code == 200, (
                f"Transition to {target} failed: {resp.status_code} {resp.text}"
            )

    async def test_01_submit_feedback_requires_authorized_role(self, client: AsyncClient):
        """Test: HR (not allowed) gets 403 when submitting feedback."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Register and advance candidate
        _, cid = await self._reg_candidate(client)
        # Run screening first to get candidate to ROUND1_PASSED
        screen_resp = await client.post("/api/screening/run", headers=hr_headers)
        assert screen_resp.status_code == 200
        await self._move_to_interview_scheduled(client, cid, admin_headers)

        # Try to submit feedback as HR — should fail (only INTERVIEWER/ADMIN allowed)
        resp = await client.post(
            f"/api/candidates/{cid}/feedback",
            headers=hr_headers,
            json={
                "technicalScore": 8,
                "communicationScore": 7,
                "recommendation": "SELECT",
                "notes": "Should be forbidden for HR",
            },
        )
        assert resp.status_code == 403, f"Expected 403 for HR, got {resp.status_code}: {resp.text}"

    async def test_02_submit_feedback_as_admin(self, client: AsyncClient):
        """Test: Admin can submit feedback and candidate transitions correctly."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Register and advance candidate
        _, cid = await self._reg_candidate(client)
        screen_resp = await client.post("/api/screening/run", headers=hr_headers)
        assert screen_resp.status_code == 200
        await self._move_to_interview_scheduled(client, cid, admin_headers)

        # Submit feedback as admin
        fb_data = {
            "technicalScore": 9,
            "communicationScore": 8,
            "recommendation": "SELECT",
            "notes": "Strong candidate, great communication",
        }
        resp = await client.post(
            f"/api/candidates/{cid}/feedback",
            headers=admin_headers,
            json=fb_data,
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "id" in data
        assert data["message"] == "Feedback submitted"

        # Verify candidate status transitioned to INTERVIEW_COMPLETED
        candidate_resp = await client.get(
            f"/api/candidates/{cid}",
            headers=admin_headers,
        )
        assert candidate_resp.status_code == 200
        assert candidate_resp.json()["status"] == "INTERVIEW_COMPLETED"

    async def test_03_get_feedback_returns_expected_data(self, client: AsyncClient):
        """Test: GET feedback returns correctly structured data."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Register and advance candidate
        _, cid = await self._reg_candidate(client)
        screen_resp = await client.post("/api/screening/run", headers=hr_headers)
        assert screen_resp.status_code == 200
        await self._move_to_interview_scheduled(client, cid, admin_headers)

        # Submit feedback
        fb_data = {
            "technicalScore": 7,
            "communicationScore": 6,
            "recommendation": "HOLD",
            "notes": "Decent candidate",
        }
        await client.post(
            f"/api/candidates/{cid}/feedback",
            headers=admin_headers,
            json=fb_data,
        )

        # Get feedback as HR
        resp = await client.get(
            f"/api/candidates/{cid}/feedback",
            headers=hr_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        fb = data[0]
        assert fb["technical"] == 7
        assert fb["communication"] == 6
        assert fb["recommendation"] == "HOLD"
        assert "comments" in fb
        assert fb["interviewer_name"] == "Admin User"
        assert "submitted_at" in fb

    async def test_04_submit_feedback_to_applied_candidate_fails(self, client: AsyncClient):
        """Test: Submitting feedback for a candidate not in INTERVIEW_SCHEDULED returns 422."""
        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert admin_login.status_code == 200
        token = admin_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Register candidate (starts as APPLIED, no screening yet)
        _, cid = await self._reg_candidate(client)

        # Try to submit feedback — candidate is APPLIED, not INTERVIEW_SCHEDULED
        resp = await client.post(
            f"/api/candidates/{cid}/feedback",
            headers=headers,
            json={
                "technicalScore": 8,
                "communicationScore": 7,
                "recommendation": "SELECT",
                "notes": "Should fail",
            },
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
        assert "INTERVIEW_SCHEDULED" in resp.json()["detail"]

    async def test_05_submit_feedback_nonexistent_candidate(self, client: AsyncClient):
        """Test: Submitting feedback for a non-existent candidate returns 404."""
        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert admin_login.status_code == 200
        token = admin_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/candidates/{fake_id}/feedback",
            headers=headers,
            json={
                "technicalScore": 8,
                "communicationScore": 7,
                "recommendation": "SELECT",
                "notes": "Should 404",
            },
        )
        assert resp.status_code == 404

    async def test_06_get_feedback_nonexistent_candidate(self, client: AsyncClient):
        """Test: Getting feedback for a non-existent candidate returns empty list."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        token = hr_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/candidates/{fake_id}/feedback",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_07_candidate_read_includes_interviewer_name(self, client: AsyncClient):
        """Test: CandidateRead.from_orm_compat correctly includes interviewer name from relationship."""
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Register and advance candidate
        _, cid = await self._reg_candidate(client)
        screen_resp = await client.post("/api/screening/run", headers=hr_headers)
        assert screen_resp.status_code == 200
        await self._move_to_interview_scheduled(client, cid, admin_headers)

        # Submit feedback
        await client.post(
            f"/api/candidates/{cid}/feedback",
            headers=admin_headers,
            json={
                "technicalScore": 8,
                "communicationScore": 9,
                "recommendation": "SELECT",
                "notes": "Excellent",
            },
        )

        # Get candidate detail — should include interview_feedback with interviewerName
        candidate_resp = await client.get(
            f"/api/candidates/{cid}",
            headers=hr_headers,
        )
        assert candidate_resp.status_code == 200
        data = candidate_resp.json()
        assert data["interview_feedback"] is not None
        assert data["interview_feedback"]["interviewerName"] == "Admin User"
        assert data["interview_feedback"]["technicalScore"] == 8
        assert data["interview_feedback"]["recommendation"] == "select"

    async def test_08_submit_feedback_lowercase_recommendation(self, client: AsyncClient):
        """Test: Frontend sends lowercase recommendation (e.g. 'select', 'hold', 'reject')
        and backend normalizes to uppercase for storage (SQLite/PostgreSQL compat).
        When read back via from_orm_compat, it appears as lowercase in candidate detail.
        """
        hr_login = await client.post("/api/auth/login", json={
            "email": "hr@knowledgefactory.com", "password": "Hr@12345",
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        admin_login = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Register and advance candidate
        _, cid = await self._reg_candidate(client)
        screen_resp = await client.post("/api/screening/run", headers=hr_headers)
        assert screen_resp.status_code == 200
        await self._move_to_interview_scheduled(client, cid, admin_headers)

        # Submit feedback with lowercase recommendation (mimics frontend behavior)
        resp = await client.post(
            f"/api/candidates/{cid}/feedback",
            headers=admin_headers,
            json={
                "technicalScore": 6,
                "communicationScore": 5,
                "recommendation": "hold",
                "notes": "Testing lowercase recommendation",
            },
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"

        # Verify recommendation was stored as "HOLD" (uppercase) by checking via GET feedback endpoint
        get_resp = await client.get(
            f"/api/candidates/{cid}/feedback",
            headers=hr_headers,
        )
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert len(data) >= 1
        fb = data[0]
        # The GET /feedback endpoint returns the raw stored value
        assert fb["recommendation"] == "HOLD", (
            f"Expected 'HOLD' (uppercase), got '{fb['recommendation']}' — "
            "recommendation case normalization failed"
        )

        # Also verify through candidate detail (which lowercases via from_orm_compat)
        candidate_resp = await client.get(
            f"/api/candidates/{cid}",
            headers=hr_headers,
        )
        assert candidate_resp.status_code == 200
        assert candidate_resp.json()["interview_feedback"]["recommendation"] == "hold"
