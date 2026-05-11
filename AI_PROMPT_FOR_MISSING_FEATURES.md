# Complete AI Prompt to Implement Missing Features

Copy and paste this prompt to another AI assistant to implement all missing features:

---

## CONTEXT

I have a Knowledge Factory Talent Hiring Portal application with:
- **Frontend**: React + TypeScript + Vite (in `app/` directory)
- **Backend**: FastAPI + Python + PostgreSQL (in `backend/` directory)
- **Current Status**: Basic candidate management, screening, and analytics are working

## CURRENT WORKING FEATURES

✅ User authentication (HR, Admin, Interviewer, Candidate roles)
✅ Candidate registration and login
✅ HR Dashboard with candidate listing and filtering
✅ Screening functionality (APPLIED → ROUND1_PASSED)
✅ Basic analytics dashboard with funnel chart
✅ CSV export of candidates

## CRITICAL ISSUES TO FIX

### Issue 1: No Assessment Workflow
**Problem**: Candidates cannot take assessments. HR cannot assign or manage assessments.

**What exists**:
- Backend routes are NOW ENABLED in `backend/app/main.py`:
  - `/api/assessment/*` (assessments)
  - `/api/code/*` (code execution)
  - `/api/questions/*` (questions)
  - `/api/proctoring/*` (proctoring)
  - `/api/interviews/*` (interviews)
  - `/api/selection/*` (selection)

**What's missing**:
1. HR interface to assign assessments to candidates
2. Candidate portal to take assessments
3. Assessment results view for HR
4. Automatic status transitions after assessment completion

### Issue 2: No Workflow to Move Candidates Through Rounds
**Problem**: Candidates are stuck at ROUND1_PASSED (eligible) status. No way to progress them through Round 2, Round 3, Interviews, and Selection.

**Expected Flow** (from `backend/app/core/enums.py`):
```
APPLIED 
  → ROUND1_PASSED (after screening)
  → ROUND2_IN_PROGRESS (assign Round 2 assessment)
  → ROUND2_PASSED (complete Round 2)
  → ROUND3_IN_PROGRESS (assign Round 3 assessment)
  → ROUND3_PASSED (complete Round 3)
  → INTERVIEW_SCHEDULED (schedule interview)
  → INTERVIEW_COMPLETED (interview done)
  → SELECTED (final selection)
```

**What's missing**:
1. Bulk actions to assign assessments
2. Individual candidate actions
3. Status transition validation
4. Automatic status updates

## TASKS TO IMPLEMENT

### PHASE 1: Assessment Assignment & Management (HIGH PRIORITY)

#### Task 1.1: Create HR Assessment Assignment Interface
**Location**: `app/src/pages/hr/AssessmentManagement.tsx` (new file)

**Requirements**:
1. Create a new page accessible from HR Dashboard
2. Show list of candidates with status ROUND1_PASSED (eligible)
3. Add bulk selection checkboxes
4. Add "Assign Round 2 Assessment" button
5. Add "Assign Round 3 Assessment" button
6. Modal to configure assessment:
   - Select assessment template (fetch from `/api/assessment/templates`)
   - Set deadline (date picker)
   - Add instructions (textarea)
7. On submit, call backend API to create assessments
8. Update candidate status automatically

**API Endpoints to Use**:
```typescript
// Fetch eligible candidates
GET /api/candidates?status=eligible

// Fetch assessment templates
GET /api/assessment/templates

// Assign assessment to candidates
POST /api/assessment/assign
Body: {
  candidate_ids: string[],
  round: "ROUND_2" | "ROUND_3",
  template_id: string,
  deadline: string,
  instructions?: string
}
```

#### Task 1.2: Create Backend Assessment Assignment Endpoint
**Location**: `backend/app/features/assessments/routes.py`

**Requirements**:
1. Add new endpoint `POST /api/assessment/assign`
2. Validate candidate IDs exist
3. Validate candidates are in correct status for the round
4. Create assessment records in database
5. Update candidate status:
   - Round 2 → `ROUND2_IN_PROGRESS`
   - Round 3 → `ROUND3_IN_PROGRESS`
6. Send notification to candidates (optional)
7. Return success response with created assessment IDs

**Example Implementation**:
```python
@router.post("/assign")
async def assign_assessment(
    data: AssessmentAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN]))
):
    # Validate candidates
    # Create assessments
    # Update candidate status
    # Return response
```

#### Task 1.3: Create Candidate Assessment Portal
**Location**: `app/src/pages/candidate/Assessment.tsx` (already exists, needs enhancement)

**Requirements**:
1. Fetch assigned assessments: `GET /api/assessment/active`
2. Show assessment details (round, deadline, status)
3. "Start Assessment" button
4. Assessment interface with:
   - Timer (countdown to deadline)
   - Problem statement panel
   - Code editor (Monaco Editor or similar)
   - Test cases panel
   - Submit button
5. Code execution: `POST /api/code/execute`
6. Submit assessment: `POST /api/assessment/{id}/submit`
7. Show results after submission

#### Task 1.4: Create HR Assessment Results View
**Location**: `app/src/pages/hr/AssessmentResults.tsx` (new file)

**Requirements**:
1. List all assessments with filters:
   - Round (Round 2, Round 3)
   - Status (Not Started, In Progress, Completed)
   - Candidate name/email search
2. Show assessment details:
   - Candidate info
   - Start time, end time, duration
   - Score/verdict
   - Code submissions
3. View candidate code submissions
4. Manual scoring interface (if needed)
5. Bulk actions:
   - Pass selected candidates (move to next round)
   - Reject selected candidates

---

### PHASE 2: Bulk Actions & Workflow (HIGH PRIORITY)

#### Task 2.1: Add Bulk Actions to HR Dashboard
**Location**: `app/src/pages/hr/Dashboard.tsx`

**Requirements**:
1. Add checkbox column to candidate table
2. Add "Select All" checkbox in header
3. Add bulk action toolbar (shows when candidates selected):
   - "Assign Round 2 Assessment"
   - "Assign Round 3 Assessment"
   - "Schedule Interview"
   - "Mark as Selected"
   - "Mark as Rejected"
4. Implement each action with confirmation modal
5. Show success/error notifications
6. Refresh table after action

#### Task 2.2: Add Individual Candidate Actions
**Location**: `app/src/pages/hr/CandidateDetail.tsx`

**Requirements**:
1. Add action buttons based on current status:
   - ROUND1_PASSED → "Assign Round 2 Assessment"
   - ROUND2_PASSED → "Assign Round 3 Assessment"
   - ROUND3_PASSED → "Schedule Interview"
   - INTERVIEW_COMPLETED → "Select" or "Reject"
2. Add status change dropdown (manual override)
3. Add notes/comments section
4. Show assessment history
5. Show interview feedback (if exists)

#### Task 2.3: Implement Status Transition Validation
**Location**: `backend/app/features/candidates/service.py`

**Requirements**:
1. Create status transition validation function
2. Define allowed transitions:
```python
ALLOWED_TRANSITIONS = {
    CandidateStatus.APPLIED: [
        CandidateStatus.ROUND1_PASSED,
        CandidateStatus.ROUND1_REJECTED,
        CandidateStatus.ROUND1_REVIEW
    ],
    CandidateStatus.ROUND1_PASSED: [
        CandidateStatus.ROUND2_IN_PROGRESS
    ],
    CandidateStatus.ROUND2_IN_PROGRESS: [
        CandidateStatus.ROUND2_PASSED,
        CandidateStatus.ROUND2_REJECTED,
        CandidateStatus.TERMINATED
    ],
    # ... etc
}
```
3. Validate transitions in `update_status()` method
4. Raise error if invalid transition attempted
5. Add override flag for HR/Admin (with audit log)

---

### PHASE 3: Interview Management (MEDIUM PRIORITY)

#### Task 3.1: Create Interview Scheduling Interface
**Location**: `app/src/pages/hr/InterviewScheduling.tsx` (new file)

**Requirements**:
1. List candidates with status ROUND3_PASSED
2. Bulk selection for interview scheduling
3. Interview scheduling form:
   - Select interviewer(s) from dropdown
   - Date and time picker
   - Interview type (Technical, HR, Managerial)
   - Meeting link (optional)
   - Notes
4. API call: `POST /api/interviews/schedule`
5. Update candidate status to INTERVIEW_SCHEDULED
6. Send notifications to candidate and interviewer

#### Task 3.2: Create Interviewer Panel
**Location**: `app/src/pages/interviewer/InterviewPanel.tsx`

**Requirements**:
1. List assigned interviews
2. Filter by date, status
3. View candidate details:
   - Resume
   - Assessment scores
   - Previous round feedback
4. Interview feedback form:
   - Technical score (1-10)
   - Communication score (1-10)
   - Recommendation (Select, Reject, Hold)
   - Detailed notes
5. Submit feedback: `POST /api/interviews/{id}/feedback`
6. Update candidate status to INTERVIEW_COMPLETED

#### Task 3.3: Backend Interview Endpoints
**Location**: `backend/app/features/interviews/routes.py`

**Requirements**:
1. `POST /api/interviews/schedule` - Schedule interview
2. `GET /api/interviews` - List interviews (with filters)
3. `GET /api/interviews/{id}` - Get interview details
4. `POST /api/interviews/{id}/feedback` - Submit feedback
5. `PATCH /api/interviews/{id}` - Update interview
6. `DELETE /api/interviews/{id}` - Cancel interview

---

### PHASE 4: Proctoring (MEDIUM PRIORITY)

#### Task 4.1: Add Proctoring to Assessment
**Location**: `app/src/pages/candidate/Assessment.tsx`

**Requirements**:
1. Request camera permission on assessment start
2. Capture webcam feed
3. Detect violations:
   - Tab switch (window blur event)
   - Multiple faces (face detection API)
   - No face detected
   - Copy/paste attempts
4. Send violation events: `POST /api/proctoring/event`
5. Show warning to candidate
6. Auto-terminate after X violations

#### Task 4.2: Proctoring Dashboard for HR
**Location**: `app/src/pages/hr/ProctoringDashboard.tsx` (new file)

**Requirements**:
1. List all proctoring events
2. Filter by:
   - Candidate
   - Assessment
   - Event type
   - Severity
3. Show violation details:
   - Timestamp
   - Event type
   - Screenshot (if captured)
   - Action taken
4. Bulk review actions

---

### PHASE 5: Selection & Final Steps (MEDIUM PRIORITY)

#### Task 5.1: Create Selection Panel
**Location**: `app/src/pages/selection/SelectionPanel.tsx`

**Requirements**:
1. List candidates with status INTERVIEW_COMPLETED
2. Show complete candidate profile:
   - Personal details
   - Assessment scores (Round 2 & 3)
   - Interview feedback
   - Overall recommendation
3. Selection actions:
   - Select (move to SELECTED)
   - Reject (move to FINAL_REJECTED)
   - Hold (keep in INTERVIEW_COMPLETED)
4. Bulk selection
5. Generate offer letter (optional)

#### Task 5.2: Backend Selection Endpoints
**Location**: `backend/app/features/selection/routes.py`

**Requirements**:
1. `GET /api/selection/candidates` - Get candidates ready for selection
2. `POST /api/selection/select` - Mark candidates as selected
3. `POST /api/selection/reject` - Mark candidates as rejected
4. `GET /api/selection/summary` - Get selection summary stats

---

### PHASE 6: Enhanced Analytics (LOW PRIORITY)

#### Task 6.1: Replace Mock Data with Real Data
**Location**: `backend/app/features/analytics/service.py`

**Requirements**:
1. Calculate real pass rates per round from database
2. Calculate real college breakdown
3. Calculate real branch performance
4. Calculate real proctoring violations
5. Remove all mock data
6. Add caching for performance

#### Task 6.2: Add More Analytics Charts
**Location**: `app/src/pages/analytics/AnalyticsDashboard.tsx`

**Requirements**:
1. Time-series chart (applications over time)
2. Assessment score distribution
3. Interview feedback trends
4. Conversion rates per stage
5. Average time per stage

---

## TECHNICAL SPECIFICATIONS

### Database Schema (if tables don't exist)

```sql
-- Assessments table
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id),
    round VARCHAR(10) NOT NULL, -- ROUND_2, ROUND_3
    template_id UUID,
    status VARCHAR(20) DEFAULT 'NOT_STARTED',
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    deadline TIMESTAMP,
    score DECIMAL(5,2),
    verdict VARCHAR(10), -- PASS, FAIL
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Assessment submissions
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

-- Interviews table
CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id),
    interviewer_id UUID REFERENCES users(id),
    scheduled_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'SCHEDULED',
    meeting_link TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Interview feedback
CREATE TABLE interview_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id),
    technical_score INT CHECK (technical_score BETWEEN 1 AND 10),
    communication_score INT CHECK (communication_score BETWEEN 1 AND 10),
    recommendation VARCHAR(20), -- SELECT, REJECT, HOLD
    detailed_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Proctoring events
CREATE TABLE proctoring_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessments(id),
    event_type VARCHAR(50),
    severity VARCHAR(20),
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);
```

### API Response Formats

```typescript
// Assessment Assignment Response
{
  "success": true,
  "assessments_created": 5,
  "candidate_ids": ["uuid1", "uuid2", ...],
  "message": "Assessments assigned successfully"
}

// Assessment List Response
{
  "data": [
    {
      "id": "uuid",
      "candidate": {
        "id": "uuid",
        "name": "John Doe",
        "email": "john@example.com"
      },
      "round": "ROUND_2",
      "status": "IN_PROGRESS",
      "score": 85.5,
      "deadline": "2026-05-15T10:00:00Z",
      "started_at": "2026-05-10T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 50,
    "total_pages": 5
  }
}
```

### Frontend Components to Create

```
app/src/
├── pages/
│   ├── hr/
│   │   ├── AssessmentManagement.tsx (NEW)
│   │   ├── AssessmentResults.tsx (NEW)
│   │   ├── InterviewScheduling.tsx (NEW)
│   │   ├── ProctoringDashboard.tsx (NEW)
│   │   └── Dashboard.tsx (ENHANCE)
│   ├── interviewer/
│   │   └── InterviewPanel.tsx (ENHANCE)
│   ├── candidate/
│   │   └── Assessment.tsx (ENHANCE)
│   └── selection/
│       └── SelectionPanel.tsx (ENHANCE)
├── components/
│   ├── assessment/
│   │   ├── AssessmentCard.tsx (NEW)
│   │   ├── CodeSubmissionViewer.tsx (NEW)
│   │   └── TestResultsPanel.tsx (NEW)
│   └── interview/
│       ├── InterviewScheduleForm.tsx (NEW)
│       └── FeedbackForm.tsx (NEW)
└── hooks/
    ├── useAssessments.ts (NEW)
    ├── useInterviews.ts (NEW)
    └── useProctoring.ts (NEW)
```

### Backend Files to Modify/Create

```
backend/app/features/
├── assessments/
│   ├── routes.py (ENHANCE - add assign endpoint)
│   ├── service.py (ENHANCE)
│   └── schemas.py (ADD new schemas)
├── interviews/
│   ├── routes.py (ENHANCE)
│   ├── service.py (ENHANCE)
│   └── schemas.py (ENHANCE)
├── proctoring/
│   ├── routes.py (ENHANCE)
│   └── service.py (ENHANCE)
├── selection/
│   ├── routes.py (ENHANCE)
│   └── service.py (ENHANCE)
└── candidates/
    ├── service.py (ADD status validation)
    └── routes.py (ADD bulk actions)
```

---

## IMPLEMENTATION ORDER

1. **Start with Phase 1, Task 1.2** (Backend assessment assignment endpoint)
2. **Then Phase 1, Task 1.1** (HR assessment assignment UI)
3. **Then Phase 1, Task 1.3** (Candidate assessment portal)
4. **Then Phase 1, Task 1.4** (HR assessment results view)
5. **Then Phase 2** (Bulk actions and workflow)
6. **Then Phase 3** (Interview management)
7. **Then Phase 4** (Proctoring)
8. **Then Phase 5** (Selection)
9. **Finally Phase 6** (Enhanced analytics)

---

## TESTING CHECKLIST

After implementation, test:
- [ ] HR can assign Round 2 assessment to eligible candidates
- [ ] Candidate receives assessment and can start it
- [ ] Candidate can write code and execute tests
- [ ] Candidate can submit assessment
- [ ] HR can view assessment results
- [ ] Candidate status updates automatically after assessment
- [ ] HR can assign Round 3 assessment to Round 2 passed candidates
- [ ] HR can schedule interviews for Round 3 passed candidates
- [ ] Interviewer can submit feedback
- [ ] HR can select/reject candidates after interview
- [ ] Bulk actions work for multiple candidates
- [ ] Status transitions are validated
- [ ] Proctoring detects violations
- [ ] Analytics show real data

---

## IMPORTANT NOTES

1. **Use existing code patterns**: Follow the patterns in `backend/app/features/candidates/` and `app/src/pages/hr/Dashboard.tsx`
2. **Reuse components**: Use existing UI components from `app/src/components/ui/`
3. **Follow authentication**: Use `require_role()` decorator for backend, `useAuth()` hook for frontend
4. **Error handling**: Add proper error handling and user-friendly messages
5. **Loading states**: Show loading spinners during API calls
6. **Validation**: Validate all inputs on both frontend and backend
7. **Database migrations**: Create Alembic migrations for new tables
8. **Type safety**: Use TypeScript types and Python type hints

---

## DELIVERABLES

1. All new files created
2. All existing files modified
3. Database migrations (if needed)
4. API documentation updated
5. README with new features documented
6. Test results showing all features working

---

## QUESTIONS TO ASK IF UNCLEAR

1. Should assessments have time limits (e.g., 60 minutes)?
2. Should proctoring auto-terminate after X violations?
3. Should there be email notifications for status changes?
4. Should interviewers see assessment scores before interview?
5. Should there be an approval workflow for selections?

---

## FILE STRUCTURE REFERENCE

Current working directory structure:
```
.
├── app/                          # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── api/                  # API client functions
│   │   ├── components/           # Reusable components
│   │   ├── contexts/             # React contexts
│   │   ├── hooks/                # Custom hooks
│   │   ├── pages/                # Page components
│   │   ├── types/                # TypeScript types
│   │   └── utils/                # Utility functions
│   └── package.json
└── backend/                      # Backend (FastAPI + Python)
    ├── app/
    │   ├── core/                 # Core utilities
    │   ├── features/             # Feature modules
    │   ├── database.py           # Database setup
    │   └── main.py               # FastAPI app
    ├── alembic/                  # Database migrations
    └── requirements.txt
```

---

## START HERE

Begin with implementing the backend assessment assignment endpoint (`POST /api/assessment/assign`) in `backend/app/features/assessments/routes.py`. This is the foundation for the entire assessment workflow.

Good luck! 🚀
