# Knowledge Factory - Setup and Implementation Guide

This document provides a comprehensive guide to setting up, running, and understanding the Knowledge Factory platform.

---

## 1. Project Overview

Knowledge Factory is an AI-powered intern hiring and evaluation platform. it streamlines the recruitment process through:
- **Multi-role Access:** Candidate, HR, Interviewer, Admin, and Superadmin.
- **Assessment Engine:** Coding challenges with real-time execution and proctoring.
- **AI Integration:** Automated question generation and evaluation.
- **Analytics:** Data-driven insights into the hiring funnel and candidate performance.

---

## 2. Setup and Run Instructions

### Prerequisites
- **Backend:** Python 3.10+, PostgreSQL (or SQLite for local dev).
- **Frontend:** Node.js 18+, npm or yarn.
- **Other:** Redis (for rate limiting/caching), Docker (optional, for code execution sandbox).

### Backend Setup (FastAPI)
1.  **Navigate to backend directory:**
    ```bash
    cd backend
    ```
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables:**
    Copy `.env.example` to `.env` and update the values:
    ```bash
    cp .env.example .env
    ```
    Key variables: `DATABASE_URL`, `JWT_SECRET_KEY`, `AI_API_KEY`, `SANDBOX_URL`.
5.  **Run Database Migrations:**
    ```bash
    alembic upgrade head
    ```
6.  **Start the Server:**
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
    The API will be available at `http://localhost:8000`. API docs at `/docs`.

### Frontend Setup (React + Vite)
1.  **Navigate to app directory:**
    ```bash
    cd app
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Configure Environment Variables:**
    Create a `.env` file (or `.env.local`):
    ```env
    VITE_API_URL=http://localhost:8000/api
    ```
4.  **Start the Development Server:**
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

---

## 3. Feature to Code Mapping

| Feature | Backend (app/features/) | Frontend (src/pages/) |
| :--- | :--- | :--- |
| **Authentication** | `auth/` (JWT, Roles, OTP) | `auth/` (Login, Register, OTP) |
| **Candidate Management** | `candidates/` (CRUD, Bulk Upload) | `hr/CandidateDetail.tsx` |
| **Assessments** | `assessments/` (Round mgmt, Submissions) | `candidate/Assessment.tsx` |
| **Code Execution** | `code_execution/` (Sandbox integration) | `components/assessment/CodeEditor.tsx` |
| **Proctoring** | `proctoring/` (Tab switches, AI flags) | Injected via hooks in Assessment page |
| **Interviews** | `interviews/` (Feedback, Scoring) | `interviewer/InterviewPanel.tsx` |
| **Selection/Hiring** | `selection/`, `hiring_cycles/` | `selection/SelectionPanel.tsx` |
| **Analytics** | `analytics/` (Funnel, Metrics) | `analytics/AnalyticsDashboard.tsx` |
| **Admin/Superadmin** | `admin/` (Org mgmt) | `superadmin/SuperAdminPanel.tsx` |
| **Audit Logs** | `audit/` (System activity) | Dashboard views |
| **Questions** | `questions/` (AI Generation, Bank) | Managed via Admin/HR views |
| **Notifications** | `notifications/` (Email, In-app) | Triggered by system events |
| **Screening** | `screening/` (Resume parsing) | Used during candidate registration |

---

## 4. API Endpoints Summary

### Auth (`/api/auth`)
- `POST /login`: Authenticate and get JWT.
- `POST /register`: Candidate registration.
- `GET /me`: Get current user info.
- `POST /verify-otp`: Verify email via OTP.

### Candidates (`/api/candidates`)
- `GET /`: List candidates with filters (status, college, etc.).
- `GET /{id}`: Detailed candidate profile.
- `PATCH /{id}/status`: Update candidate status (e.g., to 'round1').
- `POST /bulk-upload`: Preview and upload candidates via CSV.

### Assessments (`/api/assessment`)
- `POST /{id}/start`: Initialize an assessment round.
- `POST /{id}/submit-section`: Submit code for a specific problem.
- `GET /active`: List active assessments for the candidate.

### Code Execution (`/api/code`)
- `POST /run`: Run code in the sandbox (supports Python, JS, etc.).

### Analytics (`/api/analytics`)
- `GET /dashboard`: High-level metrics.
- `GET /funnel`: Hiring funnel data.

---

## 5. Execution Flow: What Happens?

### Running the Backend
1.  **Initialization:** `app.main:app` is loaded. Middleware (CORS, Audit) is initialized.
2.  **Database Connection:** SQLAlchemy connects to PostgreSQL/SQLite via `async_session_factory`.
3.  **Route Discovery:** Routers for each feature (Auth, Candidates, etc.) are registered under `/api`.
4.  **Startup Event:** Models are checked, and in SQLite mode, tables are created if they don't exist.
5.  **Request Handling:** Each request is validated via Pydantic schemas, processed in Services, and interacted with the DB via Models.

### Running the Frontend
1.  **Vite Build/Dev:** Vite compiles TypeScript and processes Tailwind CSS.
2.  **App Bootstrap:** `main.tsx` wraps the app in `QueryClientProvider`, `BrowserRouter`, `ThemeProvider`, and `AuthProvider`.
3.  **Auth Check:** `AuthProvider` checks `localStorage` for `kf_token`. If present, it fetches `/auth/me`.
4.  **Routing:** `App.tsx` defines routes. `ProtectedRoute` ensures only authorized roles can access specific views.
5.  **Data Fetching:** Custom hooks (e.g., `useCandidates`) use TanStack Query to fetch data from the backend API.

---

## 6. Detailed Setup Steps (Step-by-Step)

1.  **Clone the Repository** and navigate to the project root.
2.  **Database Setup:**
    - If using PostgreSQL: Create a database named `knowledge_factory`.
    - Update `DATABASE_URL` in `backend/.env`.
3.  **Backend Dependencies:**
    - Run `pip install -r backend/requirements.txt`.
4.  **Migrations:**
    - Run `alembic upgrade head` from the `backend/` directory.
5.  **Frontend Dependencies:**
    - Run `npm install` from the `app/` directory.
6.  **AI/Sandbox (Optional for basic UI dev):**
    - You need a valid `AI_API_KEY` for question generation features.
    - You need a `SANDBOX_URL` (like Judge0) for code execution features.
7.  **Execution:**
    - Open two terminals.
    - Terminal 1: `cd backend && uvicorn app.main:app --reload`
    - Terminal 2: `cd app && npm run dev`
