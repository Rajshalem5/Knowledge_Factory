"""
Integration test for complete assessment flow
Run with: pytest tests/test_assessment_flow.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_complete_assessment_flow():
    """Test full assessment lifecycle"""
    candidate_id = 12345
    
    # 1. Start assessment
    response = client.post(f"/api/assessment/start?candidate_id={candidate_id}")
    assert response.status_code == 200
    data = response.json()
    assessment_id = data["assessment_id"]
    assert data["candidate_id"] == candidate_id
    assert data["duration_minutes"] == 40
    
    # 2. Get questions
    response = client.get(f"/api/assessment/{assessment_id}/questions")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions["coding"]) == 2
    assert len(questions["mcq"]) == 10
    
    # Verify Monaco compatibility
    coding_q = questions["coding"][0]
    assert "boilerplate" in coding_q
    assert "visible_test_cases" in coding_q
    assert "hidden_test_cases" not in coding_q  # Should not be exposed
    
    # 3. Test code execution (Monaco run button)
    response = client.post("/api/code/execute", json={
        "code": "print('Hello World')",
        "language": "python",
        "stdin": ""
    })
    assert response.status_code == 200
    result = response.json()
    assert "stdout" in result
    
    # 4. Submit assessment
    submission = {
        "coding": [
            {
                "question_id": questions["coding"][0]["id"],
                "code": "def two_sum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return [0, 0]",
                "language": "python"
            },
            {
                "question_id": questions["coding"][1]["id"],
                "code": "def is_palindrome(s):\n    return s == s[::-1]",
                "language": "python"
            }
        ],
        "mcq_answers": {
            questions["mcq"][i]["id"]: "B" for i in range(10)
        }
    }
    
    response = client.post(
        f"/api/assessment/submit?assessment_id={assessment_id}",
        json=submission
    )
    assert response.status_code == 200
    
    # 5. Get result
    response = client.get(f"/api/assessment/result?candidate_id={candidate_id}")
    assert response.status_code == 200
    result = response.json()
    assert "total_score" in result
    assert "verdict" in result
    assert result["verdict"] in ["PASS", "FAIL"]


def test_duplicate_assessment_prevention():
    """Test that candidates cannot start multiple assessments"""
    candidate_id = 99999
    
    # Start first assessment
    response = client.post(f"/api/assessment/start?candidate_id={candidate_id}")
    assert response.status_code == 200
    
    # Try to start again - should return existing
    response = client.post(f"/api/assessment/start?candidate_id={candidate_id}")
    assert response.status_code == 200


def test_code_execution_languages():
    """Test code execution for different languages"""
    
    # Python
    response = client.post("/api/code/execute", json={
        "code": "print(2 + 2)",
        "language": "python",
        "stdin": ""
    })
    assert response.status_code == 200
    
    # Invalid language
    response = client.post("/api/code/execute", json={
        "code": "console.log('test')",
        "language": "javascript",
        "stdin": ""
    })
    assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
