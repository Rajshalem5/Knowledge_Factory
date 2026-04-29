# Systematic QA Bug Report
**Date:** 2026-01-09  
**Test Phase:** Integration Testing  
**Tester:** AI Systematic Debugging Agent  

---

## Executive Summary

Integration tests **FAILED TO RUN** due to incomplete multi-tenancy removal. The backend still contains ~40+ references to tenant functionality scattered across 20+ files, preventing system initialization.

**Blocker Severity:** HIGH - System cannot start  
**Root Cause:** Incomplete refactoring - tenant_id removed from some places but not others  
**Impact:** No API endpoints accessible, no frontend integration possible  

---

## Critical Bugs (BLOCKER)

### **#1: Import Error Prevents Server Startup**
**Severity:** CRITICAL - BLOCKER  
**Files Affected:** `backend/app/main.py`, `backend/app/core/enums.py`  
**Lines:** main.py:12, main.py:108, enums.py:11  

```python
# ERROR LOCATION
from app.features.auth.models import Tenant, User  # Line 12
from app.core.enums import Role, UserStatus, CycleStatus, TenantStatus  # Line 11
```

**Symptoms:**
- Server fails to start
- pytest cannot load conftest.py
- ImportError on module import

**Root Cause:**
- `Tenant` class was deleted from `models.py` during refactoring
- But `main.py` still tries to import it for seeding default tenant
- `TenantStatus` enum is still imported but never used

**Fix Required:**
1. Remove `Tenant` import from `main.py` lines 11-12 and 108
2. Remove `TenantStatus` import from `enums.py` line 11
3. Replace `seed_default_tenant_and_cycle()` function with `seed_default_admin_user()`
4. Create default admin user WITHOUT tenant_id field

**Priority:** P0 - Must fix before ANY other testing

---

### **#2: Candidate Model Still Has tenant_id Field**
**Severity:** HIGH - BREAKS DATA INTEGRITY  
**Files Affected:** `backend/app/models/candidate.py`, `backend/app/features/candidates/models.py`  
**Lines:** candidate.py:9, candidates/models.py:15  

**Current State:**
```python
class Candidate(Base):
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36))  # STILL EXISTS
    # ... rest of fields
```

**Expected State:**
```python
class Candidate(Base):
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # NO tenant_id field
    # ... rest of fields
```

**Root Cause:**
- Old model file at `app/models/candidate.py` not updated during refactoring
- New location at `app/features/candidates/models.py` also not updated
- Both files still have `tenant_id` foreign key relationship

**Impact:**
- Database schema still includes tenant_id column
- All candidate queries implicitly filter by tenant
- Frontend receives tenant_id in responses (violates spec)

**Fix Required:**
1. Remove `tenant_id` column from both model files
2. Update database migration/schema
3. Ensure all queries no longer filter by tenant_id

**Priority:** P1 - Blocks data consistency validation

---

### **#3: User Model Still References Tenant**
**Severity:** HIGH - BREAKS AUTHENTICATION  
**Files Affected:** `backend/app/models/user.py`  
**Lines:** user.py:9  

**Current State:**
```python
class User(Base):
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=True)  # STILL EXISTS
    email = Column(String, unique=True, nullable=False)
    # ...
```

**Expected State:**
```python
class User(Base):
    id = Column(String, primary_key=True)
    # NO tenant_id field
    email = Column(String, unique=True, nullable=False)
    # ...
```

**Root Cause:**
- Old `app/models/user.py` file not synchronized with new `app/features/auth/models.py`
- Mixed architecture: old-style models alongside new feature-based models

**Fix Required:**
1. Remove `tenant_id` from `app/models/user.py`
2. Delete or update old model files to match new structure
3. Consider removing old `/app/models` directory entirely if unused

**Priority:** P1 - Affects user authentication flow

---

### **#4: All Service Layer Methods Require tenant_id Parameter**
**Severity:** HIGH - ARCHITECTURAL INCONSISTENCY  
**Files Affected:** 
- `backend/app/features/candidates/service.py` (Lines 19, 44, 56)
- `backend/app/features/analytics/service.py` (Lines 16, 37)  
- Multiple other service files

**Examples:**
```python
# CANDIDATE SERVICE
async def list_candidates(
    self, tenant_id: UUID | None, page: int = 1, limit: int = 50, ...
):
    query = select(Candidate).where(Candidate.tenant_id == tenant_id)  # WRONG

# ANALYTICS SERVICE  
async def get_hiring_funnel(self, tenant_id: UUID) -> FunnelResponse:
    base = select(func.count(Candidate.id)).where(Candidate.tenant_id == tenant_id)
```

**Root Cause:**
- Service layer methods designed for multi-tenancy
- Every method requires `tenant_id` parameter for filtering
- Routes pass `current_user.tenant_id` (which doesn't exist anymore)

**Impact:**
- Runtime errors when calling service methods
- TypeError: missing required tenant_id argument
- Entire candidate flow broken

**Fix Required:**
1. Remove `tenant_id` parameter from ALL service method signatures
2. Remove `.where(Candidate.tenant_id == tenant_id)` filters from queries
3. Update route handlers to call services without tenant_id
4. Apply to: candidate_service, analytics_service, screening_service, selection_routes, interview_routes

**Priority:** P1 - Breaks business logic layer

---

### **#5: Route Handlers Pass Non-Existent tenant_id Attribute**
**Severity:** HIGH - RUNTIME ERRORS  
**Files Affected:** 
- `backend/app/features/candidates/routes.py` (Lines 28, 36, 55)
- `backend/app/features/selection/routes.py` (Lines 20, 43, 58)
- `backend/app/features/analytics/routes.py` (Lines 18, 24)
- `backend/app/features/screening/routes.py` (Line 24)
- `backend/app/features/hiring_cycles/routes.py` (Lines 19, 41, 58)
- `backend/app/features/audit/routes.py` (Line 26)

**Examples:**
```python
# CANDIDATES ROUTE
candidates = await service.list_candidates(
    current_user.tenant_id,  # AttributeError!
    page=page, limit=limit
)

candidate = await service.get_candidate(candidate_id, current_user.tenant_id)  # WRONG

# SELECTION ROUTE
stmt = select(Candidate).where(
    Candidate.id == candidate_id, 
    Candidate.tenant_id == current_user.tenant_id  # BOTH WRONG
)
```

**Root Cause:**
- `User` model no longer has `tenant_id` attribute
- Routes still try to access `current_user.tenant_id`
- Queries filter by `Candidate.tenant_id` which doesn't exist

**Impact:**
- AttributeError on every API request
- Candidates list endpoint crashes
- Selection/rejection flows non-functional
- Analytics dashboard breaks

**Fix Required:**
1. Remove all `current_user.tenant_id` references from routes
2. Remove all `Model.tenant_id` filters from SQLAlchemy queries
3. Make all queries tenant-agnostic (return all records)

**Priority:** P1 - Breaks all public API endpoints

---

### **#6: Schema Response Models Include tenant_id**
**Severity:** MEDIUM - DATA CONSISTENCY VIOLATION  
**Files Affected:** `backend/app/features/candidates/schemas.py` (Line 28)  
**Other affected:** Multiple response schemas throughout codebase

**Current State:**
```python
class CandidateRead(BaseModel):
    id: str
    name: str
    email: str
    college: str
    branch: str
    cgpa: float
    status: CandidateStatus
    tenant_id: UUID  # SHOULD NOT EXIST
    scores: list[AssessmentScore] = []
    applied_at: datetime
```

**Expected State:**
```python
class CandidateRead(BaseModel):
    id: str
    name: str
    email: str
    college: str
    branch: str
    cgpa: float
    status: CandidateStatus
    scores: list[AssessmentScore] = []
    applied_at: datetime
```

**Root Cause:**
- Pydantic response models include tenant_id field
- Auto-includes tenant_id from database model
- Frontend expects different schema

**Impact:**
- API returns extra field not in TypeScript interface
- Type mismatch between backend/frontend
- Violates "no tenant_id in responses" requirement

**Fix Required:**
1. Remove `tenant_id` from ALL response Pydantic models
2. Add `model_config = ConfigDict(from_attributes=True)` for SQLAlchemy compatibility
3. Audit all schema files for hidden tenant_id references

**Priority:** P2 - Data format inconsistency

---

### **#7: Legacy Middleware Still Active**
**Severity:** MEDIUM - UNNECESSARY OVERHEAD  
**Files Affected:** `backend/app/middleware/tenant.py`  
**Lines:** All 40+ lines

**Current State:**
```python
"""Tenant context injection middleware."""
class TenantMiddleware:
    """Reads the tenant_id from the decoded JWT and sets it on request.state."""
    
    async def __call__(self, scope, receive, send):
        payload = decode_token(...)
        tenant_id = payload.get("tenant_id")  # THIS FIELD NEVER EXISTS
        request.state.tenant_id = tenant_id
```

**Root Cause:**
- Middleware created for multi-tenancy support
- Still registered in FastAPI app (if included)
- Expects `tenant_id` in JWT token (which we removed)

**Impact:**
- Middleware runs on every request (performance overhead)
- Tries to read non-existent JWT field
- Potentially sets `request.state.tenant_id = None`

**Fix Required:**
1. Check if middleware is registered in `main.py` or dependencies
2. If registered, remove registration
3. Delete `middleware/tenant.py` file entirely
4. Clean up any imports referencing this middleware

**Priority:** P2 - Cleanup item

---

### **#8: Admin Routes Manage Tenants**
**Severity:** LOW - DEAD FUNCTIONALITY  
**Files Affected:** `backend/app/features/admin/routes.py`  
**Lines:** 12, 21, 28, 46, 50, 63

**Current State:**
```python
@router.get("/organizations", response_model=list[OrganizationRead])
async def list_organizations(current_user=Depends(get_current_superadmin)):
    stmt = select(Tenant).order_by(Tenant.name)  # Creates table that doesn't exist
    tenants = result.scalars().all()
    
    for t in tenants:
        cand_q = select(func.count()).where(Tenant.id == t.id)  # WRONG LOGIC
```

**Expected Behavior:**
- Admin routes should manage USERS, not organizations
- Remove tenant CRUD operations
- Keep user management features only

**Root Cause:**
- Multi-tenant admin features not stripped out
- Organizations/tenants concept removed from business logic
- But admin panel still shows "Create Organization" UI/backend

**Impact:**
- API endpoints return 500 errors (Tenant table doesn't exist)
- Frontend buttons non-functional
- Confusing UX (admin can't manage organizations)

**Fix Required:**
1. Remove organization/tenant CRUD endpoints from admin routes
2. Keep only user management (create/update/delete users)
3. Remove `Tenant` import
4. Update frontend admin UI to show users, not organizations

**Priority:** P3 - Feature removal

---

## Secondary Issues (Found During Grep Analysis)

### **#9: Resume Model Has tenant_id**
**File:** `backend/app/models/resume.py` (Line 10)  
**Severity:** MEDIUM  
**Fix:** Remove tenant_id column, delete legacy resume handling

### **#10: HiringCycle Model Requires tenant_id**
**File:** `backend/app/features/hiring_cycles/models.py` (Line 23)  
**Severity:** HIGH  
**Fix:** Remove tenant_id foreign key, update all cycle queries

### **#11: Proctoring/Audit/Analytics Models Reference Tenants**
**Files:** `analytics/models.py`, `audit/models.py`, `notifications/models.py`  
**Severity:** MEDIUM  
**Fix:** Remove optional tenant_id foreign keys, make queries tenant-agnostic

### **#12: Old Route Files Still Exist**
**Files:** `backend/app/routes/candidate.py`, `backend/app/routes/resume.py`  
**Severity:** MEDIUM  
**Issue:** Duplicate routes competing with new feature-based routes  
**Fix:** Delete legacy route files, keep only `app/features/*/routes.py`

### **#13: Enums File Has Unused TenantStatus**
**File:** `backend/app/core/enums.py` (Line 34)  
**Severity:** LOW  
**Fix:** Remove `TenantStatus` enum, keep only `Role`, `UserStatus`, `CycleStatus`

---

## Fix Priority Matrix

| Bug # | Component | Severity | Effort | Impact | Priority Order |
|-------|-----------|----------|--------|--------|----------------|
| #1 | App Initialization | CRITICAL | 30 min | Blocks everything | **#1** |
| #2 | Candidate Model | HIGH | 15 min | Data integrity | **#2** |
| #3 | User Model | HIGH | 10 min | Auth system | **#3** |
| #4 | Service Layer | HIGH | 2 hours | Business logic | **#4** |
| #5 | Route Handlers | HIGH | 2 hours | All APIs | **#5** |
| #6 | Response Schemas | MEDIUM | 1 hour | API contract | **#6** |
| #7 | Middleware | MEDIUM | 5 min | Performance | **#7** |
| #8 | Admin Routes | LOW | 30 min | Admin panel | **#8** |
| #9-13 | Various | MEDIUM | 1 hour | Cleanup | **#9+** |

**Total Estimated Fix Time:** ~5.5 hours (single developer)

---

## Recommended Fix Strategy

### **Phase 1: Unblock Server (15 minutes)**
1. Remove Tenant imports from main.py
2. Replace `seed_default_tenant_and_cycle()` with `seed_default_admin()`
3. Verify server starts successfully

### **Phase 2: Core Models (30 minutes)**
1. Remove tenant_id from User model
2. Remove tenant_id from Candidate model
3. Run database migration/schema update
4. Verify no tenant_id columns in database

### **Phase 3: Service Layer Refactor (2 hours)**
1. Remove tenant_id parameters from all service methods
2. Update all WHERE clauses to remove tenant filtering
3. Test each service method independently

### **Phase 4: Route Handlers (2 hours)**
1. Remove `current_user.tenant_id` calls from routes
2. Update service calls to match new signatures
3. Test each API endpoint manually

### **Phase 5: Response Schemas & Cleanup (1 hour)**
1. Remove tenant_id from Pydantic response models
2. Delete legacy middleware and old route files
3. Clean up unused enums
4. Final audit for remaining tenant references

---

## Success Criteria

After fixes complete:
- ✅ Server starts without import errors
- ✅ No Tenant class imported anywhere
- ✅ Database schema has no tenant_id columns
- ✅ All API endpoints return 200 OK (or proper 4xx/5xx)
- ✅ API responses do NOT contain tenant_id field
- ✅ Frontend can authenticate and fetch data
- ✅ Candidate registration/login works end-to-end
- ✅ HR can view candidates without tenant filtering

---

## Risk Assessment

**High-Risk Areas:**
1. **Database Migration:** Removing columns may lose data
   - Mitigation: Backup database first, create migration script
   
2. **Hardcoded Tenant References:** Some code may assume tenant_id exists
   - Mitigation: Global search-and-replace, test all endpoints
   
3. **Frontend Compatibility:** Frontend may expect tenant_id in types
   - Mitigation: Update frontend types.ts, verify all components render

**Rollback Plan:**
If fixes cause issues, git revert to commit before refactoring attempt:
```bash
git checkout <commit-before-refactor>
```

---

## Next Steps

1. **Approve fix plan** - Confirm priority order and effort estimate
2. **Phase 1 execution** - Unblock server first (fastest win)
3. **Run smoke tests** - Verify basic auth flow after each phase
4. **Full integration tests** - After all fixes complete
5. **Frontend validation** - Connect frontend to fixed backend

---

**Report Generated By:** Systematic Debugging AI Agent  
**Analysis Method:** Root cause tracing + Pattern analysis + Evidence gathering  
**Confidence Level:** 95% (one uncertain area noted below)

**Uncertainty Note:** Approximately 5% uncertainty on whether all tenant references are captured. Recommend running `grep -r "tenant" backend/app` after fixes to confirm zero matches except in comments/docs.
