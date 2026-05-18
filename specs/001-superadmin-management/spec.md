# Feature Specification: Super Admin Management & User Profile Settings

**Feature Branch**: `001-superadmin-management`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "there should be only one superadmin, how they are multiple admins, and also there is no option to promote admins to super admins + no profile settings panel for any role"

## User Scenarios & Testing

### User Story 1 - Profile Settings Panel (Priority: P1)

Every user — SUPERADMIN, ADMIN, HR, INTERVIEWER, and CANDIDATE — can access a settings/profile panel from anywhere in the app. The panel shows their current profile info and allows editing name, changing password, and uploading a profile photo.

**Why this priority**: Touches every user of the system. Highest UX impact. No user can currently edit their own profile.

**Independent Test**: Any logged-in user clicks their avatar/name in the sidebar or top bar → sees settings panel → can change name and password.

**Acceptance Scenarios**:
1. **Given** any logged-in user, **When** they click their avatar/name in navigation, **Then** a dropdown menu appears with "Settings" option
2. **Given** the dropdown, **When** they click "Settings", **Then** they see their profile with name (editable), email (read-only), role badge, and member-since date
3. **Given** the profile form, **When** they type a new name and click Save, **Then** the name updates everywhere in the app immediately
4. **Given** the profile form, **When** they enter current password + new password + confirm and click Save, **Then** the password is updated and they can log in with the new password
5. **Given** the profile form, **When** they upload a photo, **Then** the photo updates everywhere (sidebar, top bar, tables)
6. **Given** an invalid password change (wrong current password, mismatched confirmation, too short), **When** they submit, **Then** a clear error message explains the problem
7. **Given** a candidate user, **When** they access settings, **Then** they see the same form but their data comes from the candidates table

---

### User Story 2 - Superadmin views all platform users (Priority: P1)

The superadmin logs in and sees a complete list of all users (ADMIN, HR, INTERVIEWER, CANDIDATE) with their current roles. They can view who is a superadmin and who is an admin.

**Why this priority**: Without being able to see the user list, no management actions are possible. This is the foundation for US3.

**Independent Test**: Superadmin logs in → navigates to user management → sees paginated list of all users with name, email, role, status.

**Acceptance Scenarios**:
1. **Given** a superadmin is logged in, **When** they navigate to user management, **Then** they see a list of all users sorted by newest first
2. **Given** there are multiple admins displayed, **When** the list loads, **Then** each user shows their email, role, status, and creation date

---

### User Story 3 - Superadmin promotes an Admin to Superadmin (Priority: P1)

The superadmin selects an existing ADMIN user and promotes them to SUPERADMIN role. The system enforces that only one SUPERADMIN can exist at a time, so the current superadmin is automatically demoted to ADMIN during the transfer.

**Why this priority**: This is the core feature requested — the ability to transfer superadmin power to another admin.

**Independent Test**: Superadmin clicks "Transfer Super Admin" on an admin user → confirms → that admin becomes the new superadmin, and the acting superadmin becomes an admin.

**Acceptance Scenarios**:
1. **Given** a superadmin is viewing user list, **When** they click "Transfer Super Admin" on an ADMIN user, **Then** a confirmation dialog appears explaining the role swap
2. **Given** the confirmation dialog is shown, **When** the superadmin confirms, **Then** the target admin becomes SUPERADMIN and the acting superadmin becomes ADMIN
3. **Given** the role swap completes, **When** both users refresh, **Then** the new superadmin sees superadmin features and the demoted user sees admin features
4. **Given** a superadmin tries to promote a non-ADMIN user (HR, INTERVIEWER), **When** they click "Transfer Super Admin", **Then** an error message explains that only ADMIN users can be promoted

---

### User Story 4 - Database cleanup — single superadmin invariant (Priority: P2)

When the feature is deployed, any duplicate SUPERADMIN records in the database are cleaned up. Only one SUPERADMIN remains. If multiple exist, the oldest one is retained and the others are demoted to ADMIN.

**Why this priority**: This is a data integrity concern that prevents confusion but can be done as part of deployment.

**Independent Test**: After running the cleanup migration, only one user has role SUPERADMIN.

**Acceptance Scenarios**:
1. **Given** the database has multiple SUPERADMIN users, **When** the cleanup migration runs, **Then** only the oldest SUPERADMIN retains that role
2. **Given** the cleanup ran, **When** any user checks the users table, **Then** exactly one user has role SUPERADMIN

---

### Edge Cases

- What happens when the only superadmin tries to demote themselves without promoting someone else? Blocked with error.
- What happens if the target admin account is inactive/disabled? Blocked with explanation.
- What about existing session tokens after role change? Tokens remain valid until expiry (acceptable for v1).
- What if a user without a photo uploads nothing? Show initials avatar (existing pattern).
- What about photo file type/size limits? Validate server-side: JPEG/PNG only, max 2MB.
- What about the email field being locked? Security decision — email changes require verification flow.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a profile settings page accessible to all authenticated users
- **FR-002**: Users MUST be able to update their display name
- **FR-003**: Users MUST be able to change their password (requires current password verification)
- **FR-004**: Users MUST be able to upload a profile photo
- **FR-005**: Email MUST be displayed as read-only (changing email requires a separate verification flow)
- **FR-006**: The settings page MUST show role and member-since date
- **FR-007**: The system MUST allow SUPERADMIN to view all platform users
- **FR-008**: The system MUST allow SUPERADMIN to promote any ADMIN user to SUPERADMIN role
- **FR-009**: The system MUST demote the acting SUPERADMIN to ADMIN when they transfer the role (only one superadmin)
- **FR-010**: The system MUST prevent promotion of non-ADMIN roles to SUPERADMIN
- **FR-011**: The system MUST show a confirmation dialog before executing the role swap
- **FR-012**: The system MUST ensure exactly one SUPERADMIN exists after any role change
- **FR-013**: The system MUST handle both User (staff) and Candidate profiles via a single unified endpoint

### Key Entities

- **User**: A staff account (SUPERADMIN, ADMIN, HR, INTERVIEWER) with id, email, name, password_hash, role, status, photo_url, created_at
- **Candidate**: A candidate account with id, email, name, password_hash, photo_url, created_at (shared profile behavior with User)
- **Photo**: An uploaded avatar file stored at a known path, referenced by photo_url on the User/Candidate record

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every user can reach their settings in 2 clicks from any page
- **SC-002**: Name changes reflect immediately across the app without page reload
- **SC-003**: A superadmin can promote an admin in 2 clicks + 1 confirmation
- **SC-004**: The system never has more than one SUPERADMIN after any role change
- **SC-005**: Error messages clearly explain what went wrong and how to fix it

## Assumptions

- Existing auth system handles both User (staff) and Candidate entities — the `/api/auth/me` endpoint already resolves both
- Frontend already has a sidebar/nav with user avatar display
- Photo upload can be stored as a simple file path (for MVP; production would use S3/CDN)
- Only ADMIN users are eligible for SUPERADMIN promotion
- Password minimum length: 8 characters (industry standard)
