# Knowledge Factory — Security Audit: Changes Report

**Date:** 2026-05-17
**Audit Method:** vibe-check (benavlabs) — 17-category AI security audit

---

## 1. SECRETS EXPOSURE — Files Committed to Git

**Severity:** CRITICAL  
**Files:** `.gitignore`, `app/.env.example`, `ngrok_url.txt`

### Old Problem
The `.gitignore` did not contain `.env*` — no protection against accidentally committing `.env` files with API keys, database URLs, and secrets. If anyone ran `git add .`, all credentials would be public on GitHub.

### What We Changed
- Added `.env*` and `!.env.example` to `.gitignore`
- Added `ngrok_url.txt` to `.gitignore`
- Updated `app/.env.example` with all Clerk auth variables documented as placeholders

### New Method
All environment files are now git-ignored. The `.env.example` file acts as a complete reference for developers. Infrastructure URLs (ngrok) are also ignored.

---

## 2. ACCESS CONTROL — IDOR in Assessment Route

**Severity:** MEDIUM  
**Files:** `backend/app/features/assessments/routes.py`

### Old Problem
The `GET /api/assessment/{assessment_id}` endpoint only checked that the caller was a candidate (`CANDIDATE_ONLY`), but did not verify the assessment belonged to that candidate. A candidate could view another candidate's assessment data by guessing/changing the assessment ID.

```python
# OLD — no ownership check
stmt = select(Assessment).where(Assessment.id == assessment_id)
assessment = res.scalar_one_or_none()
if not assessment:
    raise HTTPException(status_code=404)
```

### What We Changed
Added a candidate_id ownership check before returning assessment data.

```python
# NEW — verifies the assessment belongs to the current user
if not assessment or str(assessment.candidate_id) != str(current_user.id):
    raise HTTPException(status_code=404)
```

### New Method
Every resource-scoped endpoint now verifies `current_user.id == resource.owner_id`. Returns a generic 404 (not 403) to avoid leaking whether the resource exists.

---

## 3. FILE UPLOAD VALIDATION — Magic Byte Detection

**Severity:** MEDIUM  
**Files:** `backend/app/core/file_validation.py` (NEW), `backend/app/features/candidates/routes.py`

### Old Problem
Bulk CSV upload endpoints accepted any file regardless of content. A file named `candidates.csv` could contain a binary executable, shell script, or 2GB garbage. Validation was limited to trying `.decode("utf-8")` — which passes for many non-CSV files.

### What We Changed
Created a centralized file validation utility and applied it to both bulk upload endpoints.

**New file:** `backend/app/core/file_validation.py`
- `validate_upload()` — checks file size (10MB max), detects magic bytes via `filetype`, validates UTF-8 for text files
- `secure_filename()` — generates UUID-based filenames for storage
- Allowed types: PDF, JPEG, PNG for documents; CSV/TXT/JSON for data imports

### New Method
Files are validated by actual content (magic bytes), not filename extension. Size is enforced server-side. Binary files disguised as CSV are rejected before any processing.

---

## 4. ERROR HANDLING — Sentry + Catch-All Middleware

**Severity:** LOW  
**Files:** `backend/app/core/config.py`, `backend/app/main.py`, `backend/.env.example`

### Old Problem
`sentry-sdk` was listed in `requirements.txt` but never initialized. Unhandled exceptions returned FastAPI's default 500 with no server-side logging. There was no way to know when things broke without reproducing the bug.

### What We Changed
- Added `SENTRY_DSN: str | None = None` to `Settings`
- Activated Sentry init in `main.py` (was stubbed but broken — `settings.SENTRY_DSN` didn't exist)
- Added catch-all exception middleware that logs every 500 and returns clean JSON
- Added `SENTRY_DSN` to `.env.example` for production setup

### New Method
Two-layer defense:
1. **Sentry** (production): auto-captures, groups, and traces every error with full context
2. **Catch-all middleware** (dev + prod): logs every unhandled exception server-side, returns consistent `{"detail": "Something went wrong"}` to clients

---

## 5. DEPENDENCY PINNING — Reproducible Builds

**Severity:** LOW  
**Files:** `backend/requirements.txt`

### Old Problem
Six packages used `>=` versioning instead of `==`:
- `aiosqlite>=0.19.0` → could pull any future version with breaking changes
- `asyncpg>=0.29.0`
- `pyjwt>=2.12.0`
- `sentry-sdk>=2.0.0`
- `nh3>=0.3.5`
- `python-multipart>=0.0.28`

### What We Changed
Pinned all packages to exact versions installed in the current environment:

```text
aiosqlite==0.22.1
asyncpg==0.31.0
pyjwt==2.12.1
sentry-sdk==2.60.0
nh3==0.3.5
python-multipart==0.0.28
```

### New Method
All 18 packages are now pinned to exact versions. Every install produces the same set of dependencies regardless of when or where it runs.

---

## Summary: Security Posture Change

| Area | Before | After |
|------|--------|-------|
| .gitignore | No .env protection | `.env*` ignored, `.env.example` excluded |
| File uploads | Trusted filename extension | Magic byte validation (filetype) |
| Assessment access | Any candidate → any assessment | Candidate → only own assessment |
| Error handling | Silent 500s | Sentry + logged + clean JSON |
| Dependencies | 6 packages unpinned | All 18 packages pinned |
| Frontend env docs | Missing Clerk vars | Full example file |

**Pre-production checklist:** `/mnt/hermes-shared/projects/Knowledge_Factory/PRODUCTION_CHECKLIST.md`
**Full audit reports + plans:** `/mnt/hermes-shared/projects/Knowledge_Factory/security/`
