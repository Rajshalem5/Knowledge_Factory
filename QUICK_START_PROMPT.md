# Quick Start Prompt for AI Assistant

Copy this shorter version if you want to start with just the critical features:

---

## PROJECT CONTEXT

Knowledge Factory Talent Hiring Portal - React + TypeScript frontend, FastAPI + Python backend.

**Working**: Authentication, candidate listing, screening (APPLIED → ROUND1_PASSED), basic analytics.

**Broken**: No assessment workflow. Candidates stuck at ROUND1_PASSED status. Cannot progress through Round 2, Round 3, Interviews, Selection.

---

## CRITICAL TASK: Implement Assessment Workflow

### Expected Flow
```
APPLIED → ROUND1_PASSED → ROUND2_IN_PROGRESS → ROUND2_PASSED 
→ ROUND3_IN_PROGRESS → ROUND3_PASSED → INTERVIEW_SCHEDULED 
→ INTERVIEW_COMPLETED → SELECTED
```

### What to Build

#### 1. Backend: Assessment Assignment API
**File**: `backend/app/features/assessments/routes.py`

Add endpoint:
```python
@router.post("/assign")
async def assign_assessment(
    candidate_ids: list[str],
    round: str,  # "ROUND_2" or "ROUND_3"
    deadline: datetime,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN]))
):
    # 1. Validate candidates exist and are in correct status
    # 2. Create assessment records in database
    # 3. Update candidate status to ROUND2_IN_PROGRESS or ROUND3_IN_PROGRESS
    # 4. Return success response
```

#### 2. Frontend: HR Assessment Assignment UI
**File**: `app/src/pages/hr/AssessmentManagement.tsx` (new)

Create page with:
- List of candidates with status "eligible" (ROUND1_PASSED)
- Checkboxes for bulk selection
- "Assign Round 2 Assessment" button
- "Assign Round 3 Assessment" button
- Modal with deadline picker
- API call to `/api/assessment/assign`

#### 3. Frontend: Candidate Assessment Portal
**File**: `app/src/pages/candidate/Assessment.tsx` (enhance existing)

Add:
- Fetch assigned assessments: `GET /api/assessment/active`
- Show assessment details (round, deadline, status)
- "Start Assessment" button
- Assessment interface:
  - Timer
  - Problem statement
  - Code editor (Monaco Editor)
  - Test cases
  - Submit button
- Code execution: `POST /api/code/execute`
- Submit: `POST /api/assessment/{id}/submit`

#### 4. Frontend: HR Assessment Results
**File**: `app/src/pages/hr/AssessmentResults.tsx` (new)

Create page with:
- List all assessments with filters (round, status, candidate)
- View submissions and scores
- Bulk actions: Pass/Reject candidates
- Pass → Move to next round
- Reject → Mark as rejected

#### 5. Backend: Status Transition Validation
**File**: `backend/app/features/candidates/service.py`

Add validation:
```python
ALLOWED_TRANSITIONS = {
    CandidateStatus.ROUND1_PASSED: [CandidateStatus.ROUND2_IN_PROGRESS],
    CandidateStatus.ROUND2_IN_PROGRESS: [
        CandidateStatus.ROUND2_PASSED,
        CandidateStatus.ROUND2_REJECTED
    ],
    CandidateStatus.ROUND2_PASSED: [CandidateStatus.ROUND3_IN_PROGRESS],
    # ... etc
}

def validate_status_transition(current, new):
    if new not in ALLOWED_TRANSITIONS.get(current, []):
        raise ValueError(f"Invalid transition: {current} → {new}")
```

#### 6. Frontend: Bulk Actions in HR Dashboard
**File**: `app/src/pages/hr/Dashboard.tsx` (enhance)

Add:
- Checkbox column in candidate table
- Bulk action toolbar when candidates selected
- Actions: "Assign Round 2", "Assign Round 3", "Schedule Interview", "Select", "Reject"

---

## DATABASE SCHEMA (if tables missing)

```sql
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id),
    round VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'NOT_STARTED',
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    deadline TIMESTAMP,
    score DECIMAL(5,2),
    verdict VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE assessment_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessments(id),
    problem_id UUID,
    code TEXT,
    language VARCHAR(20),
    test_results JSONB,
    score DECIMAL(5,2),
    submitted_at TIMESTAMP DEFAULT NOW()
);
```

---

## IMPLEMENTATION ORDER

1. Backend assessment assignment endpoint
2. HR assessment assignment UI
3. Candidate assessment portal
4. HR assessment results view
5. Status transition validation
6. Bulk actions in HR dashboard

---

## KEY FILES TO REFERENCE

- **Candidate Status Enum**: `backend/app/core/enums.py` (CandidateStatus)
- **Existing Patterns**: `backend/app/features/candidates/routes.py` and `app/src/pages/hr/Dashboard.tsx`
- **UI Components**: `app/src/components/ui/`
- **Auth**: Use `require_role()` (backend) and `useAuth()` (frontend)

---

## TESTING

After implementation:
1. HR assigns Round 2 assessment to eligible candidate
2. Candidate sees assessment in portal
3. Candidate completes assessment
4. HR views results and passes candidate
5. Candidate status updates to ROUND2_PASSED
6. HR assigns Round 3 assessment
7. Repeat flow

---

## START HERE

Begin with the backend assessment assignment endpoint in `backend/app/features/assessments/routes.py`. This is the foundation.

Check `FUNCTIONALITY_ISSUES.md` for complete details.
