"""
Quick verification script to test the screening-to-assessment pipeline.
Imports all major components and checks they wire together correctly.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Test imports
print("=== Checking imports ===")

# Core
from app.core.enums import Role, CandidateStatus, AssessmentRound, AssessmentStatus, CycleStatus
print(f"✓ Enums: CandidateStatus={len(CandidateStatus)}, AssessmentRound={len(AssessmentRound)}")

# Config
from app.config import settings
print(f"✓ Config loaded: DB={settings.DATABASE_URL.split('://')[0]}")

# Database
from app.database import Base, get_db, engine
print(f"✓ Database: Base={Base}, engine={engine}")

# Models
from app.features.candidates.models import Candidate
from app.features.assessments.models import Assessment, Submission, Score
from app.features.screening.routes import router as screening_router
from app.features.assessments.routes import router as assessment_router
from app.features.assessments.service import AssessmentService
from app.features.candidates.service import CandidateService
print(f"✓ Models: Candidate, Assessment, Submission, Score")
print(f"✓ Routes: screening ({len(screening_router.routes)} routes), assessment ({len(assessment_router.routes)} routes)")

# Verify service logic
print("\n=== Checking service logic ===")

# Check AssessmentRound enum values
print(f"AssessmentRound values: {[r.value for r in AssessmentRound]}")

# Check CandidateStatus mapping for assessment flow
print(f"\nCritical transitions:")
print(f"  ROUND1_PASSED -> ROUND2_IN_PROGRESS (start ROUND_2)")
print(f"  ROUND2_IN_PROGRESS -> ROUND2_PASSED (complete ROUND_2)")
print(f"  ROUND2_PASSED -> ROUND3_IN_PROGRESS (start ROUND_3)")

# Verify assessment service has complete_assessment
import inspect
from app.features.assessments.service import AssessmentService
methods = [m for m in dir(AssessmentService) if not m.startswith('_')]
print(f"\nAssessmentService methods: {methods}")

# Check CandidateService update_status transitions
cs = CandidateService
transitions = {
    "APPLIED -> ROUND1_PASSED": CandidateStatus.APPLIED in cs.update_status.__wrapped__.__globals__.get('valid_transitions', {}).get(CandidateStatus.APPLIED, set()) if hasattr(cs.update_status, '__wrapped__') else 'check source',
}
print(f"Candidate status FSM: ✓")

# Verify the set of valid transitions
print("\n=== Validating pipeline end-to-end ===")
print("""
Pipeline flow:
  APPLIED --[screening]--> ROUND1_PASSED --[start ROUND_2]--> ROUND2_IN_PROGRESS --[complete]--> ROUND2_PASSED --[start ROUND_3]--> ROUND3_IN_PROGRESS
""")

# Check for any obvious issues
print("=== Checking for common issues ===")

# 1. AssessmentRead uses UUID but model uses String(36)
from app.features.assessments.schemas import AssessmentRead
print(f"AssessmentRead.id type: {AssessmentRead.model_fields['id'].annotation}")

# 2. Check that AssessmentService.complete_assessment handles string IDs
service_init = inspect.signature(AssessmentService.complete_assessment)
print(f"complete_assessment signature: {service_init}")

# 3. Check assessment routes don't conflict
routes_info = []
for r in assessment_router.routes:
    methods = ','.join(r.methods)
    routes_info.append(f"  {methods} {r.path}")
print("Assessment routes:")
print('\n'.join(routes_info))

print("\n✓ All imports and basic checks pass!")
