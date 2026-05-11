# Knowledge Factory - Functionality Issues & Missing Features

## Critical Issues Found

### 1. **Candidate Status Management Issues**

**Problem**: Candidates are automatically moving to "SELECTED" status without going through proper assessment rounds.

**Root Cause**: 
- The screening process only moves candidates from `APPLIED` → `ROUND1_PASSED` (eligible)
- There's no workflow to move candidates through the assessment rounds (Round 2, Round 3)
- No assessment assignment or completion tracking

**Expected Flow** (from enums.py):
```
APPLIED → ROUND1_PASSED (screening) 
       → ROUND2_IN_PROGRESS (assessment assigned)
       → ROUND2_PASSED (assessment completed)
       → ROUND3_IN_PROGRESS (next assessment)
       → ROUND3_PASSED
       → INTERVIEW_SCHEDULED
       → INTERVIEW_COMPLETED
       → SELECTED
```

**Current Flow**:
```
APPLIED → ROUND1_PASSED → ??? → SELECTED (manual only)
```

**Missing Functionality**:
- No way to assign assessments to candidates
- No way to track assessment progress
- No automatic status transitions based on assessment completion
- No assessment scheduling interface for HR

---

### 2. **Assessment Conduct Functionality Missing**

**Problem**: HR has no way to conduct assessments as mentioned in the PRD.

**What's Missing**:
1. **Assessment Assignment Interface**:
   - No UI to select candidates and assign them to Round 2 or Round 3 assessments
   - No way to set assessment deadlines
   - No way to choose which questions/problems to include

2. **Assessment Management**:
   - No way to view which candidates have pending assessments
   - No way to see assessment progress (started, in-progress, completed)
   - No way to manually trigger assessment invitations

3. **Assessment Results View**:
   - No way to view candidate assessment submissions
   - No way to see code submissions and test results
   - No way to review and score assessments

4. **Backend Status**:
   - Assessment routes exist in `backend/app/features/assessments/` but are **COMMENTED OUT** in `main.py`
   - Code execution routes are **COMMENTED OUT** in `main.py`
   - Questions routes are **COMMENTED OUT** in `main.py`

---

### 3. **Missing Workflow: Moving Candidates Through Rounds**

**Problem**: No clear workflow for HR to move candidates from one round to the next.

**What's Needed**:
1. **Bulk Actions**:
   - Select multiple candidates
   - Assign to Round 2 assessment
   - Assign to Round 3 assessment
   - Schedule interviews
   - Bulk reject/select

2. **Individual Actions**:
   - Click on candidate → View details
   - Assign to specific assessment
   - Move to next round manually
   - Add notes/comments

3. **Status Transition Rules**:
   - Validate status transitions (can't skip rounds)
   - Automatic transitions when assessment is completed
   - Notifications to candidates when status changes

---

### 4. **Assessment Feature Not Enabled**

**Files Affected**:
- `backend/app/main.py` - Lines 28-32 (commented out)

**Commented Out Routes**:
```python
# from app.features.assessments.routes import router as assessments_router
# from app.features.code_execution.routes import router as code_execution_router
# from app.features.questions.routes import router as questions_router

# app.include_router(assessments_router, prefix="/api/assessment", tags=["Assessment"])
# app.include_router(code_execution_router, prefix="/api/code", tags=["Code Execution"])
# app.include_router(questions_router, prefix="/api/questions", tags=["Questions"])
```

**Impact**:
- Candidates cannot take assessments
- HR cannot create/manage assessments
- No code execution for coding problems
- No question bank management

---

### 5. **Interview Feature Not Enabled**

**Files Affected**:
- `backend/app/main.py` - Line 33 (commented out)

**Commented Out Routes**:
```python
# from app.features.interviews.routes import router as interviews_router
# app.include_router(interviews_router, prefix="/api", tags=["Interviews"])
```

**Impact**:
- Cannot schedule interviews
- Cannot record interview feedback
- Cannot move candidates to INTERVIEW_SCHEDULED status

---

### 6. **Proctoring Feature Not Enabled**

**Files Affected**:
- `backend/app/main.py` - Line 30 (commented out)

**Commented Out Routes**:
```python
# from app.features.proctoring.routes import router as proctoring_router
# app.include_router(proctoring_router, prefix="/api/proctoring", tags=["Proctoring"])
```

**Impact**:
- No proctoring during assessments
- No violation tracking
- No integrity monitoring

---

### 7. **Selection Feature Not Enabled**

**Files Affected**:
- `backend/app/main.py` - Line 34 (commented out)

**Commented Out Routes**:
```python
# from app.features/selection.routes import router as selection_router
# app.include_router(selection_router, prefix="/api/selection", tags=["Selection"])
```

---

## Missing Features from PRD

### 1. **Candidate Portal Features**
- [ ] View assigned assessments
- [ ] Take assessments (coding + MCQ)
- [ ] View assessment results
- [ ] View interview schedule
- [ ] Upload documents (resume, govt ID)
- [ ] Update profile

### 2. **HR Dashboard Features**
- [x] View all candidates (WORKING)
- [x] Filter candidates (WORKING)
- [x] Run screening (WORKING)
- [ ] **Assign assessments to candidates** (MISSING)
- [ ] **View assessment results** (MISSING)
- [ ] **Schedule interviews** (MISSING)
- [ ] **Bulk actions** (MISSING)
- [ ] **Move candidates through rounds** (MISSING)
- [x] Download CSV (WORKING)
- [ ] Bulk upload candidates (PARTIAL - preview only)

### 3. **Assessment Management**
- [ ] Create assessment templates
- [ ] Add questions to assessments
- [ ] Set time limits
- [ ] Configure proctoring rules
- [ ] View live assessment sessions
- [ ] Review submissions

### 4. **Interview Management**
- [ ] Schedule interviews
- [ ] Assign interviewers
- [ ] Record feedback
- [ ] View interview history

### 5. **Analytics Features**
- [x] Funnel chart (WORKING)
- [x] Pipeline stats (WORKING)
- [ ] Pass rate per round (PARTIAL - backend returns mock data)
- [ ] College breakdown (PARTIAL - backend returns mock data)
- [ ] Branch performance (PARTIAL - backend returns mock data)
- [ ] Proctoring violations (PARTIAL - backend returns mock data)

---

## Recommended Fix Priority

### **Phase 1: Enable Core Assessment Flow** (HIGH PRIORITY)
1. Enable assessment routes in `main.py`
2. Enable code execution routes
3. Enable questions routes
4. Create HR interface to assign assessments
5. Test candidate assessment flow

### **Phase 2: Complete Workflow** (HIGH PRIORITY)
1. Add bulk actions to HR dashboard
2. Implement status transition validation
3. Add assessment results view for HR
4. Enable automatic status transitions

### **Phase 3: Enable Interview Flow** (MEDIUM PRIORITY)
1. Enable interview routes
2. Create interview scheduling UI
3. Create interviewer feedback form
4. Add interview panel view

### **Phase 4: Enable Proctoring** (MEDIUM PRIORITY)
1. Enable proctoring routes
2. Add proctoring UI to candidate assessment
3. Add violation tracking to HR dashboard

### **Phase 5: Polish & Analytics** (LOW PRIORITY)
1. Complete analytics with real data
2. Add notifications
3. Add audit logs
4. Improve bulk upload

---

## Quick Wins

### 1. **Enable Assessment Routes** (5 minutes)
Uncomment lines in `backend/app/main.py`:
```python
from app.features.assessments.routes import router as assessments_router
from app.features.code_execution.routes import router as code_execution_router
from app.features.questions.routes import router as questions_router

app.include_router(assessments_router, prefix="/api/assessment", tags=["Assessment"])
app.include_router(code_execution_router, prefix="/api/code", tags=["Code Execution"])
app.include_router(questions_router, prefix="/api/questions", tags=["Questions"])
```

### 2. **Add Bulk Status Update** (30 minutes)
Add endpoint to update multiple candidates' status at once:
```python
@router.patch("/bulk-status")
async def bulk_update_status(
    candidate_ids: list[str],
    new_status: CandidateStatus,
    ...
)
```

### 3. **Add Assessment Assignment UI** (2 hours)
Create modal in HR dashboard to:
- Select candidates
- Choose assessment round
- Set deadline
- Assign assessment

---

## Database Schema Issues

### Missing Tables (if not created):
- [ ] `assessments` table
- [ ] `assessment_submissions` table
- [ ] `questions` table
- [ ] `test_cases` table
- [ ] `interviews` table
- [ ] `interview_feedback` table
- [ ] `proctoring_events` table

**Action**: Run database migrations to create all required tables.

---

## Summary

**Total Issues**: 7 major issues
**Missing Features**: 15+ features
**Commented Out Routes**: 6 feature modules
**Priority**: HIGH - Core assessment workflow is completely missing

**Next Steps**:
1. Enable all commented routes in `main.py`
2. Test each feature module
3. Create HR assessment assignment interface
4. Implement bulk actions
5. Add status transition validation
