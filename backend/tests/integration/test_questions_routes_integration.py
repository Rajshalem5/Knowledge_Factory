"""Integration tests for question generation and public view endpoints.

Tests POST /api/questions/generate (with mocked AI service)
and GET /api/questions/{id}/public.
"""
import uuid
import pytest
from unittest.mock import patch
from httpx import AsyncClient

from app.features.questions.schemas import Question, TestCase


def _make_sample_question(question_id: str = None) -> Question:
    """Create a sample Question object for mocking."""
    qid = question_id or f"q_{uuid.uuid4().hex[:8]}"
    return Question(
        id=qid,
        title="Array Sum",
        description="Given an array of N integers, find their sum.",
        difficulty="easy",
        boilerplate={
            "python": "def solve():\n    n = int(input())\n    arr = list(map(int, input().split()))\n    print(sum(arr))\n",
            "java": "public class Main { public static void main(String[] args) { } }",
            "cpp": "#include <iostream>\nusing namespace std;\nint main() { }",
        },
        public_test_cases=[
            TestCase(input="3\n1 2 3", expected_output="6", is_public=True),
            TestCase(input="2\n10 20", expected_output="30", is_public=True),
        ],
        private_test_cases=[
            TestCase(input="5\n1 1 1 1 1", expected_output="5", is_public=False),
            TestCase(input="1\n42", expected_output="42", is_public=False),
        ],
    )


class TestQuestionRoutes:
    """Test question generation and retrieval endpoints."""

    async def _candidate_headers(self, client: AsyncClient) -> dict:
        """Register a fresh candidate and return auth headers."""
        email = f"qtest-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Q Test", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.0,
            "passed_out_year": 2026, "language_choice": "python",
        })
        assert reg.status_code == 201, reg.text
        return {"Authorization": f"Bearer {reg.json()['access_token']}"}

    async def test_01_generate_question(self, client: AsyncClient):
        """POST /api/questions/generate returns a QuestionPublicView."""
        headers = await self._candidate_headers(client)

        with patch("app.features.questions.routes.generate_question") as mock_gen:
            mock_gen.return_value = _make_sample_question()
            resp = await client.post(
                "/api/questions/generate",
                headers=headers,
                json={
                    "topic": "arrays",
                    "difficulty": "easy",
                    "num_public_cases": 2,
                    "num_private_cases": 2,
                },
            )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["title"] == "Array Sum"
        assert data["difficulty"] == "easy"
        assert "description" in data
        assert "boilerplate" in data
        assert "python" in data["boilerplate"]
        assert "public_test_cases" in data
        assert len(data["public_test_cases"]) == 2
        # Private test cases should NOT be in the response
        assert "private_test_cases" not in data

    async def test_02_get_public_question(self, client: AsyncClient):
        """GET /api/questions/{id}/public returns the public view."""
        headers = await self._candidate_headers(client)

        # First generate a question
        with patch("app.features.questions.routes.generate_question") as mock_gen:
            sample = _make_sample_question()
            mock_gen.return_value = sample
            gen_resp = await client.post(
                "/api/questions/generate",
                headers=headers,
                json={},
            )
        assert gen_resp.status_code == 200
        question_id = gen_resp.json()["id"]

        # Fetch the public view
        resp = await client.get(
            f"/api/questions/{question_id}/public",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == question_id
        assert data["title"] == "Array Sum"
        assert "public_test_cases" in data
        assert "private_test_cases" not in data

    async def test_03_get_nonexistent_question(self, client: AsyncClient):
        """Getting a question that was never generated returns 404."""
        headers = await self._candidate_headers(client)

        resp = await client.get(
            f"/api/questions/nonexistent-id/public",
            headers=headers,
        )
        assert resp.status_code == 404, resp.text

    async def test_04_generate_requires_auth(self, client: AsyncClient):
        """Unauthenticated request returns 401."""
        resp = await client.post("/api/questions/generate", json={})
        assert resp.status_code == 401, resp.text

    async def test_05_public_view_requires_auth(self, client: AsyncClient):
        """Unauthenticated request for public view returns 401."""
        resp = await client.get("/api/questions/some-id/public")
        assert resp.status_code == 401, resp.text
