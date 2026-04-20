# Knowledge Factory API Inventory

Extracted from frontend API modules (`app/src/api/*.ts`). All calls proxy to `${VITE_API_URL}/api` or `/api`.

## Auth APIs (`auth.ts`)
| Method | Endpoint | Description | Params/Body |
|--------|----------|-------------|-------------|
| POST | `/auth/register` | Register user (+ resume multipart) | `{name, email, password, resume?:File}` |
| POST | `/auth/login` | Login | `{email, password}` |
| POST | `/auth/verify-otp` | Verify OTP | `{email, otp}` |
| POST | `/auth/forgot-password` | Forgot password | `{email}` |
| POST | `/auth/reset-password` | Reset password | `{token, password}` |
| GET | `/auth/me` | Get current user | - |

## Analytics APIs (`analytics.ts`)
| Method | Endpoint | Description | Params/Body |
|--------|----------|-------------|-------------|
| GET | `/analytics/funnel` | Funnel data | `?organizationId` |
| GET | `/analytics/dashboard` | Dashboard analytics | `?organizationId` |
| GET | `/superadmin/organizations` | List organizations | - |
| PATCH | `/superadmin/organizations/{id}` | Update organization | `Partial<Organization>` |

## Assessment APIs (`assessment.ts`)
| Method | Endpoint | Description | Params/Body |
|--------|----------|-------------|-------------|
| POST | `/assessment/{assessmentId}/start` | Start assessment | - |
| POST | `/assessment/{assessmentId}/submit-section` | Submit code section | `{problemId, code}` |
| GET | `/assessment/{assessmentId}` | Get assessment | - |
| GET | `/assessment/active` | Active assessments | - |
| POST | `/candidates/{candidateId}/feedback` | Submit feedback | `{technicalScore, communicationScore, recommendation, notes}` |

## Candidates APIs (`candidates.ts`)
| Method | Endpoint | Description | Params/Body |
|--------|----------|-------------|-------------|
| GET | `/candidates` | List candidates | `?page,pageSize,status,branch,college,search` |
| GET | `/candidates/{id}` | Get candidate | - |
| GET | `/candidates/me` | Get self | - |
| PATCH | `/candidates/{id}/status` | Update status | `{status}` |
| POST | `/api/candidates/bulk-upload` | Bulk upload CSV | `FormData(file)` |

## Base Client (`client.ts`)
Generic `api.{get|post|put|patch|delete}`(endpoint, options) using fetch + Bearer token.

## Backend Migration Guide
**Move to Backend (Server-Side Only)**:
- DB: Models for User, Candidate (w/ resume), Assessment, Result, Organization, Feedback.
- Auth: bcrypt/JWT, email/OTP (Nodemailer/Twilio).
- Logic: Code execution sandbox (Docker?), analytics queries, bulk parse.
- Endpoints: Implement above routes w/ validation (Zod), auth guards (HR-only feedback etc.).
- Stack: Express/NestJS + Prisma/Sequelize + PostgreSQL + Redis(sessions).

**Frontend Keeps**:
- UI (React/Vite), charts, code editor, local timers/drafts.

Implement backend to handle these 20+ endpoints.

