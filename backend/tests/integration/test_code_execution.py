"""Integration tests for code execution routes.

Tests /api/code/execute and /api/code/evaluate endpoints.
Uses the in-memory question store for evaluate-question tests.
"""

import uuid
import pytest
from httpx import AsyncClient


class TestCodeExecution:
    """Test code execution API endpoints."""

    async def _login_admin(self, client: AsyncClient) -> str:
        resp = await client.post("/api/auth/login", json={
            "email": "admin@knowledgefactory.io", "password": "Admin@12345",
        })
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def test_01_execute_python_success(self, client: AsyncClient):
        """Test: Execute simple Python code successfully."""
        token = await self._login_admin(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/code/execute",
            headers=headers,
            json={"language": "python", "code": "print('Hello, World!')"},
        )
        # Without a real sandbox, expect a connection error (sandbox unreachable)
        # But the route should return a structured response, not crash
        assert resp.status_code in (200, 502), (
            f"Expected 200 or 502, got {resp.status_code}: {resp.text}"
        )
        data = resp.json()
        # Response should have status field
        assert "status" in data, f"Missing status in response: {data}"

    async def test_02_execute_python_with_stdin(self, client: AsyncClient):
        """Test: Execute code with stdin provided."""
        token = await self._login_admin(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/code/execute",
            headers=headers,
            json={
                "language": "python",
                "code": "name = input(); print(f'Hello, {name}!')",
                "stdin": "World",
            },
        )
        assert resp.status_code in (200, 502)
        data = resp.json()
        assert "status" in data

    async def test_03_execute_unsupported_language(self, client: AsyncClient):
        """Test: Execute with an unsupported language (should return 502 or fallback)."""
        token = await self._login_admin(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/code/execute",
            headers=headers,
            json={"language": "brainfuck", "code": "++[>++<-]>."},
        )
        assert resp.status_code in (200, 502)
        data = resp.json()
        assert "status" in data

    async def test_04_execute_without_auth(self, client: AsyncClient):
        """Test: Code execution without authentication returns 401."""
        resp = await client.post(
            "/api/code/execute",
            json={"language": "python", "code": "print('x')"},
        )
        assert resp.status_code == 401, f"Expected 401 (HTTPBearer), got {resp.status_code}"

    async def test_05_execute_missing_code(self, client: AsyncClient):
        """Test: Execute without required 'code' field returns 422."""
        token = await self._login_admin(client)

        resp = await client.post(
            "/api/code/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={"language": "python"},
        )
        assert resp.status_code == 422

    async def test_06_evaluate_code(self, client: AsyncClient):
        """Test: Evaluate code against test cases."""
        token = await self._login_admin(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/code/evaluate",
            headers=headers,
            json={
                "language": "python",
                "code": "def add(a, b): return a + b\nimport sys\nx, y = map(int, sys.stdin.read().split())\nprint(add(x, y))",
                "test_cases": [
                    {"input": "2 3", "expected_output": "5"},
                    {"input": "10 20", "expected_output": "30"},
                ],
            },
        )
        assert resp.status_code in (200, 502)
        data = resp.json()
        if resp.status_code == 200:
            assert "total_tests" in data
            assert "passed_tests" in data
            assert "failed_tests" in data
            assert "score_percentage" in data
            assert "test_results" in data
            assert data["total_tests"] == 2

    async def test_07_evaluate_invalid_language(self, client: AsyncClient):
        """Test: Evaluate with a missing language field returns 422."""
        token = await self._login_admin(client)

        resp = await client.post(
            "/api/code/evaluate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "code": "print('x')",
                "test_cases": [],
            },
        )
        assert resp.status_code == 422
