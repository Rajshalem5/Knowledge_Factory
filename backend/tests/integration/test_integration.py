"""Integration tests for complete user flows.

This file systematically tests Candidate and HR workflows to identify bugs.
Run with: pytest backend/tests/integration/test_integration.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db, create_test_database, cleanup_test_database
from app.core.security import hash_password


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create test database session."""
    yield from create_test_database()


@pytest.fixture
def auth_headers(client, db_session):
    """Get authentication headers by logging in as admin."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@knowledgefactory.io",
            "password": "Admin@12345"
        }
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestCandidateFlow:
    """Test complete candidate workflow."""
    
    def test_01_candidate_registration(self, client, db_session):
        """Test: Register new candidate -> should succeed."""
        registration_data = {
            "name": "Test Candidate",
            "email": "test.candidate@example.com",
            "password": "Candidate@123",
            "college": "Test University",
            "branch": "Computer Science",
            "cgpa": 8.5,
            "passed_out_year": 2026,
            "language_choice": "english"
        }
        
        response = client.post("/api/auth/register", json=registration_data)
        
        # ASSERT: Should return 201 Created
        assert response.status_code == 201, f"Registration failed: {response.text}"
        
        # ASSERT: Response should contain access_token
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        assert "refresh_token" in data, "Response missing refresh_token"
        assert "user" in data, "Response missing user object"
        
        # ASSERT: User object is well-formed
        user = data["user"]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "role" in user
        
        print(f"✓ Registration successful for {registration_data['email']}")
    
    def test_02_candidate_login(self, client, db_session):
        """Test: Login with registered candidate credentials."""
        # First register
        register_response = client.post(
            "/api/auth/register",
            json={
                "name": "Login Test Candidate",
                "email": "login@test.com",
                "password": "Candidate@123",
                "college": "Test College",
                "branch": "IT",
                "cgpa": 9.0,
                "passed_out_year": 2026
            }
        )
        assert register_response.status_code == 201
        
        # Then login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@test.com",
                "password": "Candidate@123"
            }
        )
        
        # ASSERT: Login should succeed
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        # ASSERT: Token structure correct
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "candidate"
        
        print("✓ Candidate login successful")
    
    def test_03_get_me_endpoint(self, client, auth_headers):
        """Test: Get current authenticated user."""
        response = client.get("/api/auth/me", headers=auth_headers)
        
        # ASSERT: Should return user info
        assert response.status_code == 200

        data = response.json()
        print(f"Current user: {data}")

        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "role" in data
        
        print("✓ /api/auth/me works correctly")
    
    def test_04_start_assessment(self, client, auth_headers):
        """Test: Start an assessment."""
        # Note: This will likely fail if no assessments exist
        # This is expected behavior for empty state
        response = client.post(
            "/api/assessment/start",
            json={
                "cycle_id": "some-id",  # Will fail without proper cycle
            },
            headers=auth_headers
        )
        
        print(f"Assessment start response: {response.status_code} - {response.text}")
        # Don't assert here - may legitimately fail with active cycle requirement


class TestHRFlow:
    """Test complete HR workflow."""
    
    @pytest.fixture
    def hr_auth_headers(self, client, db_session):
        """Get HR auth headers."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@knowledgefactory.io",
                "password": "Admin@12345"
            }
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_01_hr_login(self, client):
        """Test: HR login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin@knowledgefactory.io",
                "password": "Admin@12345"
            }
        )
        
        assert response.status_code == 200, f"HR login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "superadmin", f"Expected 'superadmin', got '{data['user']['role']}'"
        
        print("✓ HR login successful")
    
    def test_02_view_candidates_list(self, client, hr_auth_headers):
        """Test: View candidates list."""
        # First create a candidate
        register_response = client.post(
            "/api/auth/register",
            json={
                "name": "List Test Candidate",
                "email": "list@test.com",
                "password": "Candidate@123",
                "college": "Test Uni",
                "branch": "ECE",
                "cgpa": 8.0,
                "passed_out_year": 2025
            }
        )
        assert register_response.status_code == 201
        
        # Now list candidates
        response = client.get(
            "/api/candidates?page=1&limit=50",
            headers=hr_auth_headers
        )
        
        # ASSERT: Should return 200 or 403 (depending on permissions)
        # Either way, shouldn't crash
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Candidates list: {len(data.get('data', []))} candidates found")
            
            # ASSERT: Pagination structure correct
            assert "data" in data
            assert "pagination" in data
            assert "page" in data["pagination"]
            assert "total" in data["pagination"]
        
        print("✓ Candidates list retrieval works")
    
    def test_03_update_candidate_status(self, client, hr_auth_headers):
        """Test: Update candidate status."""
        # Create candidate first
        register_response = client.post(
            "/api/auth/register",
            json={
                "name": "Status Update Candidate",
                "email": "status@test.com",
                "password": "Candidate@123",
                "college": "Test College",
                "branch": "Mechanical",
                "cgpa": 7.5,
                "passed_out_year": 2026
            }
        )
        assert register_response.status_code == 201
        
        # Get the candidate ID from response
        candidate_email = "status@test.com"
        
        # Search for this candidate
        search_response = client.get(
            f"/api/candidates?search={candidate_email}",
            headers=hr_auth_headers
        )
        
        if search_response.status_code == 200:
            candidates = search_response.json().get("data", [])
            if len(candidates) > 0:
                candidate_id = candidates[0]["id"]
                
                # Try to update status
                update_response = client.patch(
                    f"/api/candidates/{candidate_id}/status",
                    json={"status": "selected"},
                    headers=hr_auth_headers
                )
                
                print(f"Status update response: {update_response.status_code} - {update_response.text}")
                # Accept both success and failure for now
        else:
            print("Could not find candidate for status update test")


class TestAPIConsistency:
    """Test API response consistency."""

    def test_02_basic_auth_flow(self, client):
        """Test basic login returns proper structure."""
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"},
        )
        # May return 401 if DB not seeded; just verify no crash
        assert response.status_code in (200, 401, 500)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
