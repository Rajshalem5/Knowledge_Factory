"""Integration tests for question generation and retrieval routes.

Tests POST /api/questions/generate and GET /api/questions/{id}/public.
"""

import uuid
import pytest
from httpx import AsyncClient


class TestQuestionsRoutes:
    """Test question generation and retrieval."""

    async def _login_candidate(self, client: AsyncClient) -> str:
        email = f"q-{uuid.uuid4().hex[:8]}@test.com"
        reg = await client.post("/api/auth/register", json={
            "name": "Question Test", "email": email, "password": "Candidate@123",
            "college": "Test Uni", "branch": "CSE", "cgpa": 8.5,
            "passed_out_year": 2026, "language_choice": "python",
        })
        assert reg.status_code == 201, reg.text
        return reg.json()["access_token"]

    async def test_01_generate_question(self, client: AsyncClient):
        """Test: Generate a question via AI endpoint."""
        token = await self._login_candidate(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/questions/generate",
            headers=headers,
            json={
                "topic": "Two Sum",
                "difficulty": "easy",
                "num_public_cases": 2,
                "num_private_cases": 2,
            },
        )
        # Without a real AI backend, expect 502 (AI generation failed)
        # But the route should handle it gracefully
        assert resp.status_code in (200, 502), (
            f"Expected 200 or 502, got {resp.status_code}: {resp.text}"
        )

    async def test_02_generate_question_without_auth(self, client: AsyncClient):
        """Test: Generating a question without auth returns 401."""
        resp = await client.post(
            "/api/questions/generate",
            json={"topic": "test", "difficulty": "easy"},
        )
        assert resp.status_code == 401

    async def test_03_generate_question_empty_body(self, client: AsyncClient):
        """Test: Generating with an empty body passes defaults and tries AI."""
        token = await self._login_candidate(client)
        resp = await client.post(
            "/api/questions/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        # All fields have defaults, so validation passes, then tries AI
        assert resp.status_code in (200, 502)

    async def test_04_get_question_not_found(self, client: AsyncClient):
        """Test: Getting a non-existent question returns 404."""
        token = await self._login_candidate(client)
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/questions/{fake_id}/public",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
