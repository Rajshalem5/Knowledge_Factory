# Tasks: Super Admin Management & User Profile Settings

**Input**: Design documents from `specs/001-superadmin-management/`

**Prerequisites**: plan.md (complete), spec.md (complete)

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **Story**: User story this task belongs to
- Include exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migrations, directory setup, and router wiring required by all stories

- [ ] T001 Add `photo_url` column to User model in `backend/app/features/auth/models.py`
- [ ] T002 [P] Add `photo_url` column to Candidate model in `backend/app/features/candidates/models.py`
- [ ] T003 Create avatar upload directory at `backend/uploads/avatars/`
- [ ] T004 Import and wire superadmin_router in `backend/app/main.py`

**Checkpoint**: Foundation ready — both features can now be built independently

---

## Phase 2: Foundational — Profile Settings Backend (User Story 1)

**Purpose**: Backend endpoints that power the profile settings panel

**Independent Test**: `curl -X PATCH http://localhost:8000/api/auth/me -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"name":"New Name"}'` returns updated user

- [ ] T005 [P] [US1] Add `update_profile()` method to `backend/app/features/auth/service.py` (handles both User + Candidate records)
- [ ] T006 [P] [US1] Add `change_password()` method to `backend/app/features/auth/service.py`
- [ ] T007 [US1] Add `PATCH /api/auth/me` endpoint in `backend/app/features/auth/routes.py`
- [ ] T008 [US1] Add `POST /api/auth/change-password` endpoint in `backend/app/features/auth/routes.py`
- [ ] T009 [US1] Add `POST /api/auth/upload-photo` endpoint in `backend/app/features/auth/routes.py`

**Checkpoint**: Profile settings backend complete — testable via curl

---

## Phase 3: Frontend — Profile Settings Panel (User Story 1)

**Purpose**: Shared settings page accessible to all roles

**Independent Test**: Any logged-in user clicks avatar → "Settings" → sees and edits their profile

- [ ] T010 [P] [US1] Create settings API client in `app/src/pages/settings/api.ts`
- [ ] T011 [P] [US1] Create `useProfile` TanStack Query hook in `app/src/hooks/useProfile.ts`
- [ ] T012 [US1] Create `SettingsPage.tsx` in `app/src/pages/settings/` with:
  - Avatar upload section with click-to-upload
  - Name edit field
  - Read-only email display
  - Role badge and member-since date
  - Password change section (current + new + confirm)
- [ ] T013 [US1] Add "Settings" dropdown to Sidebar/TopBar — avatar click → dropdown → "Settings" menu item
- [ ] T014 [US1] Add settings route in `app/src/App.tsx`

**Checkpoint**: Every user can access and edit their profile

---

## Phase 4: Backend — Superadmin User Listing (User Story 2)

**Purpose**: Superadmin can view all platform users

**Independent Test**: Superadmin logs in → `GET /api/superadmin/users` returns all users

- [ ] T015 [P] [US2] Create `SuperAdminService` with `list_all_users()` in `backend/app/features/superadmin/service.py`
- [ ] T016 [US2] Rewrite `backend/app/features/superadmin/routes.py` — ORM-based `GET /api/superadmin/users` endpoint

**Checkpoint**: Superadmin sees all users, ready for action column

---

## Phase 5: Frontend — Superadmin User Listing (User Story 2)

**Purpose**: Superadmin can see all users in the UI

**Independent Test**: Superadmin navigates to Super Admin panel → sees all users sorted by date

- [ ] T017 [P] [US2] Create superadmin API client in `app/src/pages/superadmin/api.ts`
- [ ] T018 [US2] Update `SuperAdminPanel.tsx` — switch from `/api/admin/users` to `/api/superadmin/users`

**Checkpoint**: SuperAdminPanel shows all users via its own endpoint

---

## Phase 6: Backend — Superadmin Transfer (User Story 3)

**Purpose**: Role swap endpoint with validation

**Independent Test**: `curl -X POST http://localhost:8000/api/superadmin/users/{admin_id}/transfer -H "Authorization: Bearer <superadmin_token>"` → demotes current superadmin, promotes target

- [ ] T019 [US3] Add `transfer_superadmin()` method to `SuperAdminService` in `backend/app/features/superadmin/service.py` with validation:
  - Target exists → 404
  - Target role == ADMIN → 422
  - Target status == ACTIVE → 422
  - Target != current user → 422
  - Execute: demote current SUPERADMIN → ADMIN, promote target → SUPERADMIN
- [ ] T020 [US3] Add `POST /api/superadmin/users/{id}/transfer` endpoint in `backend/app/features/superadmin/routes.py`

**Checkpoint**: Transfer works via curl

---

## Phase 7: Frontend — Superadmin Transfer UI (User Story 3)

**Purpose**: Superadmin can transfer role from the UI

**Independent Test**: Superadmin clicks "Transfer Super Admin" on admin row → confirms → role swap executes

- [ ] T021 [P] [US3] Add `transferSuperadmin()` to superadmin API client at `app/src/pages/superadmin/api.ts`
- [ ] T022 [P] [US3] Create `TransferModal.tsx` in `app/src/pages/superadmin/` with:
  - Shows target user name and email
  - Explains: "You will be demoted to ADMIN. This action cannot be undone."
  - Confirm button + Cancel button
  - Loading state during API call
  - Success/error toast
- [ ] T023 [US3] Update `SuperAdminPanel.tsx` — add Actions column with "Transfer Super Admin" button:
  - Visible only for ADMIN rows
  - Hidden for own row
  - Hidden for SUPERADMIN/HR/INTERVIEWER/CANDIDATE rows
  - Triggers TransferModal on click

**Checkpoint**: Full transfer flow works end-to-end in the UI

---

## Phase 8: Database Cleanup & Polish

**Purpose**: Data integrity and final verification

- [ ] T024 Run SQL cleanup to demote duplicate superadmins in `knowledge_factory.db`
- [ ] T025 Verify all endpoints work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies
```
Phase 1 (Setup) ─── blocks ──→ Phase 2 (Profile Backend)
                              └─→ Phase 4 (Superadmin Backend - US2)

Phase 2 ── blocks ──→ Phase 3 (Profile Frontend)
Phase 3 ── independent of Phases 4-7

Phase 4 ── blocks ──→ Phase 5 (Superadmin Frontend - US2)
Phase 5 ── blocks ──→ Phase 6 (Superadmin Backend - US3)
Phase 6 ── blocks ──→ Phase 7 (Superadmin Frontend - US3)

Phase 8 ── final
```

### Parallel Opportunities

- T001 + T002 + T003 + T004 can run in parallel (Phase 1)
- T005 + T006 can run in parallel (Phase 2)
- T010 + T011 can run in parallel (Phase 3)
- T015 (Phase 4) can run in parallel with Phase 3
- T017 (Phase 5) can run in parallel with Phase 6
- T021 + T022 can run in parallel (Phase 7)

### Implementation Strategy (Recommended Order)

1. Phase 1 (Setup) — 4 quick tasks, 1-2min each
2. Phase 2 (Profile Backend) — backend auth endpoints
3. Phase 3 (Profile Frontend) — settings page
4. Phase 4+5 (Superadmin US2 backend + frontend) — user listing
5. Phase 6+7 (Superadmin US3 backend + frontend) — transfer flow
6. Phase 8 — cleanup + verify
