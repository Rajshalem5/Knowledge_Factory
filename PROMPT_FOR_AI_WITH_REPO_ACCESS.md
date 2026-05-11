# Complete Prompt for AI with Repository Access

Copy this prompt to an AI assistant that can read your entire codebase (like Cursor AI, GitHub Copilot, or Claude with file access):

---

## TASK: Analyze Repository and Implement All Missing Features

I have a **Knowledge Factory Talent Hiring Portal** application with a React + TypeScript frontend and FastAPI + Python backend. 

### YOUR MISSION

1. **Read the PRD** (`Knowledge Factory -Talent Hiring Portal (Product UseCase Document) (1).pdf`)
2. **Analyze the entire repository** to understand:
   - Current implementation status
   - Working features
   - Broken features
   - Missing features
   - Non-working endpoints
   - Incomplete logic
   - Database schema gaps
3. **Compare PRD requirements vs actual implementation**
4. **Create a comprehensive implementation plan**
5. **Implement all missing features**

---

## STEP 1: DISCOVERY & ANALYSIS

### Read These Files First:

1. **PRD Document**:
   - `Knowledge Factory -Talent Hiring Portal (Product UseCase Document) (1).pdf`
   - Extract all feature requirements
   - Note all user roles and their capabilities
   - Understand the complete workflow

2. **Current Issues Documentation**:
   - `FUNCTIONALITY_ISSUES.md` (I've already identified some issues)
   - Use this as a starting point, but find MORE issues

3. **Backend Structure**:
   - `backend/app/main.py` - Check which routes are enabled/disabled
   - `backend/app/core/enums.py` - Understand status enums and workflows
   - `backend/app/features/*/routes.py` - Check all feature endpoints
   - `backend/app/features/*/service.py` - Check business logic
   - `backend/app/features/*/models.py` - Check database models
   - `backend/app/features/*/schemas.py` - Check API schemas

4. **Frontend Structure**:
   - `app/src/pages/` - Check all page components
   - `app/src/api/` - Check API client functions
   - `app/src/hooks/` - Check custom hooks
   - `app/src/types/` - Check TypeScript types
   - `app/APIs.md` - Check API inventory

5. **Database**:
   - `backend/alembic/versions/` - Check migrations
   - Look for missing tables mentioned in code but not in migrations

---

## STEP 2: IDENTIFY ALL ISSUES

Create a comprehensive report covering:

### A. Missing Features (from PRD)
- List every feature mentioned in PRD
- Mark which ones are implemented ✅
- Mark which ones are missing ❌
- Mark which ones are partially implemented ⚠️

### B. Broken Endpoints
- Test all API endpoints (mentally or actually)
- Identify endpoints that:
  - Return errors
  - Have incomplete logic
  - Are missing required fields
  - Don't match frontend expectations
  - Have incorrect status codes

### C. Incomplete Workflows
- Map out expected workflows from PRD
- Compare with actual implementation
- Identify gaps in:
  - Candidate journey (registration → selection)
  - HR workflows (screening → assessment → interview → selection)
  - Interviewer workflows
  - Admin workflows

### D. Database Issues
- Check if all required tables exist
- Check if relationships are properly defined
- Check if indexes are missing
- Check if constraints are missing

### E. Frontend Issues
- Missing pages
- Broken components
- API calls that fail
- Missing UI for backend features
- Incorrect data handling

### F. Logic Errors
- Status transition validation
- Permission checks
- Data validation
- Error handling
- Edge cases

---

## STEP 3: PRIORITIZE ISSUES

Categorize all issues into:

### 🔴 CRITICAL (Blocks core functionality)
- Features that prevent the system from working
- Security vulnerabilities
- Data corruption risks

### 🟡 HIGH (Important but system works)
- Missing major features from PRD
- Incomplete workflows
- Poor user experience

### 🟢 MEDIUM (Nice to have)
- UI improvements
- Performance optimizations
- Additional features

### ⚪ LOW (Future enhancements)
- Advanced analytics
- Notifications
- Reporting

---

## STEP 4: CREATE IMPLEMENTATION PLAN

For each issue, provide:

1. **Issue Description**: What's broken/missing
2. **Root Cause**: Why it's broken/missing
3. **Impact**: What doesn't work because of this
4. **Solution**: How to fix it
5. **Files to Modify**: Exact file paths
6. **Code Changes**: Specific code to add/modify
7. **Testing**: How to verify the fix
8. **Dependencies**: What else needs to be fixed first

---

## STEP 5: IMPLEMENT FIXES

Implement in this order:

### Phase 1: Foundation (Critical Issues)
1. Fix database schema issues
2. Enable all required backend routes
3. Fix broken endpoints
4. Add missing API endpoints
5. Fix status transition logic

### Phase 2: Core Workflows (High Priority)
1. Complete candidate registration flow
2. Complete screening workflow
3. Implement assessment assignment
4. Implement assessment taking
5. Implement assessment results
6. Implement interview scheduling
7. Implement interview feedback
8. Implement selection process

### Phase 3: UI & UX (High Priority)
1. Create missing pages
2. Add missing components
3. Implement bulk actions
4. Add proper error handling
5. Add loading states
6. Add success/error notifications

### Phase 4: Advanced Features (Medium Priority)
1. Proctoring system
2. Enhanced analytics
3. Notifications
4. Audit logs
5. Reporting

### Phase 5: Polish (Low Priority)
1. Performance optimizations
2. UI/UX improvements
3. Additional features
4. Documentation

---

## SPECIFIC AREAS TO INVESTIGATE

### 1. Candidate Status Management
**Check**:
- `backend/app/core/enums.py` - CandidateStatus enum
- `backend/app/features/candidates/service.py` - Status update logic
- `backend/app/features/screening/service.py` - Screening logic
- Are status transitions validated?
- Can candidates skip rounds?
- Are there orphaned statuses?

### 2. Assessment Workflow
**Check**:
- `backend/app/features/assessments/` - All files
- `app/src/pages/candidate/Assessment.tsx` - Assessment UI
- `app/src/pages/hr/` - HR assessment management
- Can HR assign assessments?
- Can candidates take assessments?
- Can HR view results?
- Are scores calculated correctly?

### 3. Interview Management
**Check**:
- `backend/app/features/interviews/` - All files
- `app/src/pages/interviewer/` - Interviewer UI
- `app/src/pages/hr/` - Interview scheduling
- Can HR schedule interviews?
- Can interviewers submit feedback?
- Are interviews linked to candidates?

### 4. Code Execution
**Check**:
- `backend/app/features/code_execution/` - All files
- Is Piston API configured correctly?
- Are test cases executed?
- Are results returned properly?
- Is error handling complete?

### 5. Questions & Problem Bank
**Check**:
- `backend/app/features/questions/` - All files
- Can HR create questions?
- Can questions be assigned to assessments?
- Are test cases stored properly?
- Is AI question generation working?

### 6. Proctoring
**Check**:
- `backend/app/features/proctoring/` - All files
- Are proctoring events captured?
- Are violations tracked?
- Is there a proctoring dashboard?

### 7. Analytics
**Check**:
- `backend/app/features/analytics/` - All files
- `app/src/pages/analytics/` - Analytics UI
- Is data real or mocked?
- Are calculations correct?
- Are all charts working?

### 8. Authentication & Authorization
**Check**:
- `backend/app/features/auth/` - All files
- `backend/app/core/rbac.py` - Role-based access control
- `backend/app/dependencies.py` - Auth dependencies
- Are all roles properly checked?
- Can users access unauthorized endpoints?
- Is token refresh working?

### 9. Database Relationships
**Check**:
- All `models.py` files
- Are foreign keys defined?
- Are relationships bidirectional?
- Are cascade deletes configured?
- Are indexes on foreign keys?

### 10. Frontend-Backend Integration
**Check**:
- `app/src/api/` - All API client files
- Do API calls match backend endpoints?
- Are request/response types correct?
- Is error handling consistent?
- Are loading states handled?

---

## EXPECTED DELIVERABLES

### 1. Analysis Report
```markdown
# Knowledge Factory - Complete Analysis Report

## Executive Summary
- Total features in PRD: X
- Implemented features: Y
- Missing features: Z
- Broken features: W

## Critical Issues (🔴)
1. [Issue name]
   - Description: ...
   - Impact: ...
   - Solution: ...
   - Files: ...

## High Priority Issues (🟡)
...

## Medium Priority Issues (🟢)
...

## Low Priority Issues (⚪)
...

## Implementation Roadmap
- Phase 1: [Timeline]
- Phase 2: [Timeline]
- Phase 3: [Timeline]
...
```

### 2. Implementation Plan
For each issue, provide:
- Detailed solution
- Code snippets
- File paths
- Testing instructions

### 3. Code Implementation
- All new files created
- All existing files modified
- Database migrations (if needed)
- Tests (if applicable)

### 4. Testing Report
- What was tested
- Test results
- Known issues
- Workarounds

---

## IMPORTANT GUIDELINES

### Code Quality
- Follow existing code patterns in the repo
- Use TypeScript types (frontend)
- Use Python type hints (backend)
- Add proper error handling
- Add input validation
- Add logging where appropriate

### Security
- Validate all inputs
- Check permissions on all endpoints
- Prevent SQL injection
- Prevent XSS attacks
- Use parameterized queries
- Hash passwords properly

### Performance
- Add database indexes where needed
- Optimize queries
- Add caching where appropriate
- Lazy load data
- Paginate large lists

### User Experience
- Add loading states
- Add error messages
- Add success notifications
- Add confirmation dialogs for destructive actions
- Make UI responsive

### Testing
- Test happy paths
- Test error cases
- Test edge cases
- Test with different user roles
- Test with invalid data

---

## QUESTIONS TO ANSWER

As you analyze the codebase, answer these questions:

1. **Candidate Journey**:
   - Can a candidate register? ✅/❌
   - Can a candidate login? ✅/❌
   - Can a candidate see assigned assessments? ✅/❌
   - Can a candidate take assessments? ✅/❌
   - Can a candidate see results? ✅/❌
   - Can a candidate see interview schedule? ✅/❌

2. **HR Workflows**:
   - Can HR view all candidates? ✅/❌
   - Can HR filter candidates? ✅/❌
   - Can HR run screening? ✅/❌
   - Can HR assign assessments? ✅/❌
   - Can HR view assessment results? ✅/❌
   - Can HR schedule interviews? ✅/❌
   - Can HR select/reject candidates? ✅/❌
   - Can HR perform bulk actions? ✅/❌

3. **Interviewer Workflows**:
   - Can interviewer see assigned interviews? ✅/❌
   - Can interviewer view candidate details? ✅/❌
   - Can interviewer submit feedback? ✅/❌

4. **Admin Workflows**:
   - Can admin manage users? ✅/❌
   - Can admin manage hiring cycles? ✅/❌
   - Can admin view analytics? ✅/❌

5. **Assessment System**:
   - Are assessment templates defined? ✅/❌
   - Can assessments be assigned? ✅/❌
   - Can code be executed? ✅/❌
   - Are test cases run? ✅/❌
   - Are scores calculated? ✅/❌
   - Are results stored? ✅/❌

6. **Status Transitions**:
   - Are transitions validated? ✅/❌
   - Can candidates skip rounds? ✅/❌
   - Are transitions automatic? ✅/❌
   - Are transitions logged? ✅/❌

---

## EXAMPLE OUTPUT FORMAT

```markdown
## Issue #1: Assessment Assignment Not Working

**Priority**: 🔴 CRITICAL

**Description**: 
HR cannot assign assessments to candidates. The endpoint exists but the UI is missing.

**Root Cause**:
- Backend endpoint `/api/assessment/assign` exists but is not fully implemented
- Frontend has no UI to trigger this endpoint
- No validation for candidate eligibility

**Impact**:
- Candidates cannot progress beyond ROUND1_PASSED status
- Assessment workflow is completely blocked
- HR cannot conduct Round 2 or Round 3 assessments

**Solution**:

1. **Backend Fix** (`backend/app/features/assessments/routes.py`):
```python
@router.post("/assign")
async def assign_assessment(
    data: AssessmentAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN]))
):
    # Validate candidates
    candidates = await db.execute(
        select(Candidate).where(Candidate.id.in_(data.candidate_ids))
    )
    candidates = candidates.scalars().all()
    
    if not candidates:
        raise HTTPException(404, "No candidates found")
    
    # Validate status
    for candidate in candidates:
        if data.round == "ROUND_2" and candidate.status != CandidateStatus.ROUND1_PASSED:
            raise HTTPException(400, f"Candidate {candidate.id} not eligible for Round 2")
    
    # Create assessments
    assessments = []
    for candidate in candidates:
        assessment = Assessment(
            candidate_id=candidate.id,
            round=data.round,
            deadline=data.deadline,
            status=AssessmentStatus.NOT_STARTED
        )
        db.add(assessment)
        
        # Update candidate status
        if data.round == "ROUND_2":
            candidate.status = CandidateStatus.ROUND2_IN_PROGRESS
        elif data.round == "ROUND_3":
            candidate.status = CandidateStatus.ROUND3_IN_PROGRESS
        
        assessments.append(assessment)
    
    await db.commit()
    
    return {
        "success": True,
        "assessments_created": len(assessments),
        "candidate_ids": data.candidate_ids
    }
```

2. **Frontend UI** (`app/src/pages/hr/AssessmentManagement.tsx`):
```typescript
// [Complete component code here]
```

3. **Testing**:
- Login as HR
- Navigate to Assessment Management
- Select candidates with ROUND1_PASSED status
- Click "Assign Round 2 Assessment"
- Set deadline
- Submit
- Verify assessments created in database
- Verify candidate status updated to ROUND2_IN_PROGRESS

**Files Modified**:
- `backend/app/features/assessments/routes.py`
- `backend/app/features/assessments/schemas.py` (add AssessmentAssignRequest)
- `app/src/pages/hr/AssessmentManagement.tsx` (new file)
- `app/src/api/assessment.ts` (add assignAssessment function)
- `app/src/App.tsx` (add route)

**Dependencies**:
- None (can be implemented immediately)
```

---

## START YOUR ANALYSIS NOW

1. Read the PRD document thoroughly
2. Explore the entire codebase systematically
3. Create the analysis report
4. Prioritize issues
5. Create implementation plan
6. Start implementing fixes

**Be thorough. Be detailed. Find EVERYTHING that's broken or missing.**

I want a complete, production-ready implementation that matches the PRD requirements 100%.

---

## ADDITIONAL CONTEXT

- **Current Status**: Basic features work (auth, candidate listing, screening)
- **Known Issues**: Assessment workflow missing, no interview management, candidates stuck at ROUND1_PASSED
- **Backend**: All routes are now enabled in `main.py` (I just fixed this)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: React 18 + TypeScript + Vite
- **Code Editor**: Monaco Editor (for assessment code editor)
- **Code Execution**: Piston API (configured in .env)

Read `FUNCTIONALITY_ISSUES.md` for issues I've already identified, but **find more issues** by analyzing the entire codebase against the PRD.

Good luck! 🚀
