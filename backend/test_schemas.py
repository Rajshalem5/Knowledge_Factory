"""Test Pydantic UUID coercion with actual ORM model."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# MUST import Candidate first to resolve relationships
from app.features.candidates.models import Candidate
from app.features.assessments.schemas import AssessmentRead
from app.features.assessments.models import Assessment
from app.features.candidates.schemas import CandidateRead
from app.core.enums import AssessmentRound, AssessmentStatus
import uuid
from datetime import datetime, timezone, timedelta

# Test 1: Can we create AssessmentRead from an ORM object?
assessment = Assessment(
    id=str(uuid.uuid4()),
    candidate_id=str(uuid.uuid4()),
    round=AssessmentRound.ROUND_2,
    questions_json={},
    link_token=uuid.uuid4().hex,
    link_expiry=datetime.now(timezone.utc) + timedelta(days=5),
    started_at=datetime.now(timezone.utc),
    status=AssessmentStatus.IN_PROGRESS,
)

try:
    read = AssessmentRead.model_validate(assessment, from_attributes=True)
    print(f"✓ AssessmentRead from ORM: id={read.id}, type={type(read.id).__name__}")
except Exception as e:
    print(f"✗ AssessmentRead from ORM FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Can we create AssessmentRead from a dict (as JSON)?
try:
    read2 = AssessmentRead.model_validate({
        "id": str(uuid.uuid4()),
        "candidate_id": str(uuid.uuid4()),
        "round": "ROUND_2",
        "status": "IN_PROGRESS",
        "questions_json": {},
        "link_token": "abc",
        "link_expiry": "2026-05-15T00:00:00+00:00",
        "started_at": "2026-05-10T00:00:00+00:00",
        "time_limit": 60,
    })
    print(f"✓ AssessmentRead from dict: id={read2.id}, type={type(read2.id).__name__}")
except Exception as e:
    print(f"✗ AssessmentRead from dict FAILED: {e}")

# Test 3: Check CandidateRead UUID coercion
candidate = Candidate(
    id=str(uuid.uuid4()),
    name="Test",
    email="test@test.com",
    college="Test Uni",
    branch="CSE",
    cgpa=8.5,
    passed_out_year=2026,
    language_choice="python",
    status="APPLIED",
    cycle_id=str(uuid.uuid4()),
)
candidate.created_at = datetime.now(timezone.utc)

try:
    read3 = CandidateRead.from_orm_compat(candidate)
    print(f"✓ CandidateRead from ORM: id={read3.id}, type={type(read3.id).__name__}")
    print(f"  display_status={read3.display_status}, status={read3.status}")
except Exception as e:
    print(f"✗ CandidateRead from ORM FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ All schema tests complete!")
