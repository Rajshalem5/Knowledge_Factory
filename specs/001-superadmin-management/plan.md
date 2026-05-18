# Implementation Plan: Super Admin Management & User Profile Settings

**Branch**: `dev` | **Date**: 2026-05-18 | **Spec**: `specs/001-superadmin-management/spec.md`

## Summary

Two independent features in one cycle:
1. **Profile Settings Panel** (P1) — shared settings page for ALL roles (staff + candidates). Edit name, change password, upload photo.
2. **Superadmin Management** (P1) — wire dead backend routes, DB cleanup, frontend transfer UI.

## Technical Context

**Language/Version**: Python 3.12 (FastAPI), TypeScript 5.x (React + Vite)

**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.0 async, aiosqlite, PyJWT, python-multipart (for file upload)
- Frontend: React, TanStack Query, React Router v6, Tailwind CSS

**Storage**: SQLite (`knowledge_factory.db`), avatar files at `backend/uploads/avatars/`

**Testing**: curl + browser verification

## Constitution Check

**GATE: Passed** — no violations

## Project Structure

```
specs/001-superadmin-management/
├── spec.md
├── plan.md                # This file
├── tasks.md               # Generated next
└── contracts/
    └── api-contracts.md   # API contracts for new endpoints
```

### Backend Changes

```
backend/app/
├── main.py                            # + import superadmin_router + include
├── features/
│   ├── superadmin/
│   │   ├── __init__.py
│   │   ├── routes.py                  # REWRITE — ORM-based, add transfer endpoint
│   │   └── service.py                 # NEW — transfer_superadmin() logic
│   ├── candidates/models.py           # +photo_url column (ALTER TABLE)
│   └── auth/
│       ├── models.py                  # +photo_url column (ALTER TABLE)
│       ├── routes.py                  # +PATCH /me, +POST /change-password, +POST /upload-photo
│       └── service.py                 # +update_profile(), +change_password()
└── uploads/avatars/                   # NEW — avatar storage directory
```

### Frontend Changes

```
app/src/
├── pages/settings/
│   ├── SettingsPage.tsx               # NEW — shared settings panel for all roles
│   └── api.ts                         # NEW — API client for profile endpoints
├── pages/superadmin/
│   ├── SuperAdminPanel.tsx            # MODIFY — add action column
│   ├── TransferModal.tsx              # NEW — confirmation dialog
│   └── api.ts                         # NEW — API client for superadmin endpoints
├── components/layout/
│   ├── Sidebar.tsx                    # MODIFY — add user avatar click → dropdown → Settings
│   └── TopBar.tsx                     # MODIFY — same
└── hooks/
    └── useProfile.ts                  # NEW — TanStack Query hook for own profile
```

## Phase Breakdown

### Phase 1: Backend — Profile Settings Endpoints

**Files**: `auth/routes.py`, `auth/service.py`, `auth/models.py`, `candidates/models.py`

Three new endpoints on the existing auth router:

```
PATCH /api/auth/me          — Update name, photo_url
  Body: { "name": "New Name" }
  Response: { "id", "email", "name", "role", "photo_url" }
  Auth: Any authenticated user (via get_current_user)

POST /api/auth/change-password  — Change password
  Body: { "current_password": "...", "new_password": "...", "confirm_password": "..." }
  Response: { "message": "Password updated" }
  Auth: Any authenticated user

POST /api/auth/upload-photo     — Upload avatar
  Body: multipart/form-data with "photo" field (JPEG/PNG, max 2MB)
  Response: { "photo_url": "/uploads/avatars/<uuid>.jpg" }
  Auth: Any authenticated user
```

**Service layer** in `auth/service.py`:
- `update_profile(user_id, data)` — handles both User and Candidate records
- `change_password(user_id, current_pw, new_pw)` — verify + hash + update

**DB migration**: ALTER TABLE users ADD COLUMN photo_url; ALTER TABLE candidates ADD COLUMN photo_url

### Phase 2: Frontend — Profile Settings UI

**Files**: `settings/SettingsPage.tsx`, `settings/api.ts`, `hooks/useProfile.ts`, `Sidebar.tsx`, `TopBar.tsx`

Settings page layout:
```
[Avatar Section]
  ┌──────┐
  │  A   │  Click to upload
  │      │  JPEG/PNG, max 2MB
  └──────┘

[Profile Form]
  Full Name:  [___________]
  Email:      admin@...  (read-only, greyed out)
  Role:       ADMIN       (badge)
  Joined:     May 2026

[Security Section]
  Current Password:  [___________]
  New Password:      [___________]
  Confirm Password:  [___________]

  [Cancel]  [Save Changes]
```

### Phase 3: Backend — Superadmin Transfer

**Files**: `superadmin/service.py` (NEW), `superadmin/routes.py` (REWRITE), `main.py`

```
GET  /api/superadmin/users                  — List all users (replaces /api/admin/users for superadmin)
POST /api/superadmin/users/{id}/transfer    — Transfer superadmin role
```

**Validation** in `transfer_superadmin()`:
1. Target exists → 404
2. Target role == ADMIN → 422
3. Target status == ACTIVE → 422
4. Target != current user → 422
5. Execute: demote current SUPERADMIN → ADMIN, promote target → SUPERADMIN

### Phase 4: Frontend — Superadmin Transfer UI

**Files**: `superadmin/SuperAdminPanel.tsx`, `superadmin/TransferModal.tsx`, `superadmin/api.ts`

Add action column to users table. "Transfer Super Admin" button on ADMIN rows only. Opens modal with explanation and CONFIRM flow.

### Phase 5: DB Cleanup

Run SQL to demote duplicate superadmins:
```sql
UPDATE users SET role = 'ADMIN'
WHERE role = 'SUPERADMIN'
AND id != (SELECT id FROM users WHERE role = 'SUPERADMIN' ORDER BY created_at ASC LIMIT 1);
```

## Verification Plan

1. Profile: PATCH /api/auth/me → name updates
2. Profile: POST /api/auth/change-password → password changes, old password stops working
3. Profile: POST /api/auth/upload-photo → photo URL returned
4. Transfer: POST /api/superadmin/users/{admin_id}/transfer → swap works
5. Transfer: POST /api/superadmin/users/{hr_id}/transfer → 422
6. Transfer: POST /api/superadmin/users/{self}/transfer → 422
7. Cleanup: Exactly one SUPERADMIN in DB
