# ACCESS_CONTROL Security Report

## Status: MEDIUM

## Findings

### MEDIUM: `GET /api/assessment/{assessment_id}` — Missing ownership check

**File**: `backend/app/features/assessments/routes.py` (lines 42-52)

```python
@router.get("/{assessment_id}", response_model=AssessmentRead)
async def get_assessment_by_id(assessment_id: str, ..., current_user = Depends(CANDIDATE_ONLY)):
    stmt = select(Assessment).where(Assessment.id == assessment_id)
    res = await db.execute(stmt)
    assessment = res.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment
```

This route only verifies the caller is a candidate (`CANDIDATE_ONLY`) but does **not** verify that `assessment.candidate_id == current_user.id`. A candidate could access another candidate's assessment data by guessing the UUID.

**Risk**: Low in practice (UUIDs are hard to guess), but violates the principle of least privilege and the IDOR checklist requirement.

### PASS: Other assessment routes properly scope to user

- `start_assessment/candidate_id` — uses `current_user.id` from auth context
- `get_active_assessments` — scoped to `current_user.id`
- `complete_assessment` — passes `current_user.id` to service which verifies ownership
- `submit_section` — service verifies `assessment.candidate_id == candidate_id`

### PASS: HR/Admin routes

HR, ADMIN, and SUPERADMIN routes are intentionally designed to access any candidate's data — this is correct for their role.

### PASS: Candidate routes

Candidates access their own profile via `/candidates/me` which is scoped by `get_current_user`. HR routes that access candidates by ID are properly role-gated.

## What's at risk

A malicious candidate could potentially view another candidate's assessment details, questions, and status by iterating UUIDs (though UUIDs are practically unguessable).

## What's already secure

- Most routes properly scope to `current_user.id`
- Service layer enforces ownership checks on write operations
- HR routes are properly role-gated
- JWT-based auth makes it impossible to impersonate other users

## Recommendations

1. **[MEDIUM]** Add ownership check to `GET /api/assessment/{assessment_id}`: verify `assessment.candidate_id == current_user.id`
2. **[LOW]** Consider auditing all routes with resource IDs for consistent ownership checks
