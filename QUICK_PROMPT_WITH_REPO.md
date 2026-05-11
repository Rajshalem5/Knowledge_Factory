# Quick Prompt for AI with Repository Access

Use this shorter version for AI assistants with codebase access (Cursor, Copilot, Claude with files):

---

## TASK: Analyze & Fix Knowledge Factory Talent Hiring Portal

### Step 1: Read & Understand
1. **Read PRD**: `Knowledge Factory -Talent Hiring Portal (Product UseCase Document) (1).pdf`
2. **Read current issues**: `FUNCTIONALITY_ISSUES.md`
3. **Explore codebase**:
   - Backend: `backend/app/features/*/` (all feature modules)
   - Frontend: `app/src/pages/*/` (all pages)
   - API: `app/src/api/*.ts` (API clients)
   - Database: `backend/alembic/versions/` (migrations)

### Step 2: Identify Issues
Compare PRD requirements vs actual implementation. Find:
- ❌ Missing features
- 🐛 Broken endpoints
- ⚠️ Incomplete logic
- 🔴 Non-working workflows
- 📊 Missing database tables
- 🎨 Missing UI components

### Step 3: Create Report
List all issues with:
- Description
- Root cause
- Impact
- Solution
- Files to modify
- Priority (Critical/High/Medium/Low)

### Step 4: Implement Fixes
Fix in priority order:
1. **Critical**: Database schema, broken endpoints, security issues
2. **High**: Assessment workflow, interview management, status transitions
3. **Medium**: Proctoring, enhanced analytics, bulk actions
4. **Low**: UI polish, notifications, reporting

---

## Key Areas to Check

### 1. Candidate Journey (APPLIED → SELECTED)
- Registration ✅/❌
- Screening ✅/❌
- Assessment assignment ✅/❌
- Assessment taking ✅/❌
- Interview scheduling ✅/❌
- Selection ✅/❌

### 2. Assessment Workflow
- Can HR assign assessments? ✅/❌
- Can candidates take assessments? ✅/❌
- Can HR view results? ✅/❌
- Are scores calculated? ✅/❌
- Do status transitions work? ✅/❌

### 3. Interview Management
- Can HR schedule interviews? ✅/❌
- Can interviewers submit feedback? ✅/❌
- Are interviews linked to candidates? ✅/❌

### 4. Status Transitions
- Are transitions validated? ✅/❌
- Can candidates skip rounds? ✅/❌
- Are transitions automatic? ✅/❌

### 5. Database
- All required tables exist? ✅/❌
- Relationships defined? ✅/❌
- Indexes on foreign keys? ✅/❌

### 6. API Endpoints
- All endpoints working? ✅/❌
- Request/response match? ✅/❌
- Error handling complete? ✅/❌

---

## Expected Output

### 1. Analysis Report
```
# Issues Found

## Critical (🔴)
1. Assessment assignment not working
   - Backend endpoint incomplete
   - Frontend UI missing
   - Fix: [detailed solution]

## High (🟡)
2. Interview scheduling missing
   - No UI for HR
   - Backend endpoint exists but incomplete
   - Fix: [detailed solution]

...
```

### 2. Implementation
- Create missing files
- Fix broken files
- Add database migrations
- Test all changes

---

## Start Here

1. Read PRD document
2. Explore `backend/app/features/` and `app/src/pages/`
3. Compare PRD vs implementation
4. List ALL issues
5. Implement fixes in priority order

**Be thorough. Find everything that's broken or missing.**

I want a complete, production-ready system that matches the PRD 100%.

---

## Context

- **Working**: Auth, candidate listing, screening, basic analytics
- **Broken**: Assessment workflow, interview management, status transitions
- **Backend**: FastAPI + Python + PostgreSQL
- **Frontend**: React + TypeScript + Vite
- **Routes**: All enabled in `backend/app/main.py`

Check `FUNCTIONALITY_ISSUES.md` for known issues, but **find more** by analyzing against PRD.
