# Knowledge Factory Hiring Platform - Setup & Overview

## SECTION 1 – PROJECT OVERVIEW

### Project Name
Knowledge Factory Hiring Platform

### Purpose
To streamline and automate the entire technical hiring process—from resume screening and initial coding assessments to AI-driven proctoring and final HR selection.

### Business Problem Solved
Traditional hiring is time-consuming, prone to bias, and difficult to scale. This platform automates the initial funnel (resume parsing, objective assessments) while ensuring integrity via advanced AI proctoring, allowing HR to focus solely on high-quality, verified candidates.

### Key Features
*   **AI-Powered Screening:** Automatic resume parsing and eligibility checks based on hiring cycle rules.
*   **Dynamic Assessments:** AI-generated coding questions and multi-section evaluations (MCQ + Code).
*   **Real-time AI Proctoring:** WebSocket-based continuous monitoring for tab switches, face detection, phone detection, and audio analysis.
*   **Code Execution Engine:** Secure sandbox environment for running candidate submissions.
*   **Comprehensive Analytics:** Hiring funnel tracking and dashboard metrics.

### User Roles
1.  **Candidate:** Applies for jobs, takes assessments, views results.
2.  **Interviewer:** Reviews candidate submissions, conducts interviews, submits feedback.
3.  **HR:** Manages hiring cycles, reviews candidates, makes selection decisions.
4.  **Admin:** System configuration, user management (HR/Interviewers).
5.  **SuperAdmin:** Cross-organization oversight, global configuration.

### High-Level Architecture
The system is built on a modern, decoupled architecture:
*   **Frontend:** React Single Page Application (SPA).
*   **Backend:** FastAPI providing RESTful APIs and WebSocket endpoints.
*   **AI Proctoring Service:** Dedicated microservice for processing audio/video streams using computer vision and LLMs.
*   **Code Sandbox:** Piston-based execution engine for safely evaluating untrusted code.

### Technology Stack
*   **Frontend:** React, TypeScript, Vite, TailwindCSS (assumed standard), React Router.
*   **Backend:** Python 3.10+, FastAPI, SQLAlchemy 2.0 (Async), SQLite (Dev) / PostgreSQL (Prod), Alembic.
*   **Database:** SQLite / PostgreSQL.
*   **AI Services:** OpenRouter (LLM routing), HuggingFace models, YOLO (Object Detection), Whisper (Speech-to-Text).
*   **Assessment Engine:** Piston for secure code execution.
*   **Proctoring System:** WebSockets, OpenCV, ONNX Runtime.

---

## SECTION 7 – LOCAL DEVELOPMENT SETUP

### Prerequisites
*   Node.js 18+
*   Python 3.10+
*   Git
*   Docker (Optional, but recommended for code execution engine)

### Step-by-Step Instructions

#### 1. Clone Repository
```bash
git clone <repository_url>
cd HIRING_PLATFORM
```

#### 2. Configure Environment Variables
Copy the example environment files and fill in your keys.
```bash
cp .env.example .env
cp audi_video/.env.example audi_video/.env
```
*(See `.env.example` file for details on required variables).*

#### 3. Backend Setup (Windows)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Backend Setup (Linux/MacOS)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Database Initialization & Seed Data
```bash
# Inside the backend directory with venv activated
python create_tables.py
python seed_db.py
```

#### 5. Frontend Setup
```bash
cd ../app
npm install
```

#### 6. AI Proctoring Setup (Optional for basic flow)
```bash
cd ../audi_video
python -m venv venv
# Activate venv as above
pip install -r requirements.txt
```

---

## SECTION 8 – RUNNING THE PROJECT

### Running the Backend
```bash
cd backend
# Ensure venv is activated
uvicorn app.main:app --reload --port 8000
```
*Backend Swagger UI:* `http://localhost:8000/docs`

### Running the Frontend
```bash
cd app
npm run dev
```
*Frontend URL:* `http://localhost:5173`

### Running the Proctoring Service
```bash
cd audi_video
# Ensure venv is activated
uvicorn app.main:app --reload --port 8001
```

---

## SECTION 10 – ASSESSMENT ENGINE

### Workflow Overview
1.  **Generation:** AI generates a question based on topic/difficulty with public and private test cases.
2.  **Assignment:** Candidate is assigned the assessment based on their hiring cycle.
3.  **Execution:** Candidate writes code and clicks "Run" (evaluates against public cases only).
4.  **Submission:** Candidate submits the code. The backend evaluates it against both public and private test cases via the Piston engine.
5.  **Evaluation:** Score is calculated based on test case pass rate, code quality, and efficiency.
6.  **Progression:** Candidate transitions to the next phase based on the score.

### Status Transitions
`APPLIED` → `ROUND1_PASSED` (Screening) → `ROUND2_IN_PROGRESS` → `ROUND2_PASSED` → `INTERVIEW_SCHEDULED` → `INTERVIEW_COMPLETED` → `SELECTED` / `REJECTED`

---

## SECTION 11 – PROCTORING DOCUMENTATION

### Architecture
The proctoring system uses a real-time WebSocket connection between the frontend and the FastAPI backend. The frontend captures frames and audio, sending them or pre-processed events to the backend.

### WebSocket Flow
1.  Session initialized via `/api/proctoring/session`.
2.  Frontend connects to `/ws/proctor/{session_id}` using the provided JWT token.
3.  Frontend sends events (e.g., `TAB_SWITCH`, `WINDOW_BLUR`) and periodic video frames.
4.  Backend AI service analyzes frames for multiple faces, phones, etc.
5.  Risk score is updated dynamically.

### Detection Categories & Weights
*   **Tab Switch:** Base weight 10, escalates with frequency.
*   **Window Blur:** Base weight 5.
*   **Phone Detected:** Weight 80 (Immediate high risk).
*   **Multiple Persons:** Weight 25.
*   **No Face:** Weight 15.

### Risk Management
The system maintains a cumulative `final_risk_score`. If the score exceeds the `RISK_TERMINATION_THRESHOLD` (default 100) and `HIGH_RISK_AUTO_TERMINATE` is true, the assessment is forcibly terminated.

---

## SECTION 12 – AUTHENTICATION

### JWT Flow
*   **Login:** Returns an `access_token` in the JSON response and a `refresh_token` as an `httpOnly` cookie.
*   **API Calls:** `access_token` is sent in the `Authorization: Bearer <token>` header.
*   **Refresh:** The frontend calls `/api/auth/refresh` when a 401 occurs; the backend uses the `httpOnly` cookie to issue a new `access_token`.

### Role Permissions
*   **Candidate:** Can view own profile, take assessments, view own results.
*   **Interviewer:** Can view assigned candidates, submit interview feedback.
*   **HR:** Can view all candidates, initiate Phase 2, view results, make final decisions.
*   **Admin:** Can manage hiring cycles, HR users, and interviewers.
*   **SuperAdmin:** Unrestricted access across the platform.

---

## SECTION 15 – MAINTENANCE GUIDE

### Adding New APIs
1.  Create routes in `backend/app/features/<module>/routes.py`.
2.  Include the router in `backend/app/main.py`.
3.  Add the corresponding frontend API call in `app/src/api/<module>.ts`.

### Database Migrations
Always use Alembic when modifying `models.py`:
```bash
cd backend
alembic revision --autogenerate -m "Description of change"
alembic upgrade head
```

### Logging & Monitoring
*   Logs are output to standard out (`stdout`) and file (`backend_log.txt`).
*   Audit logs for administrative actions are stored in the `audit_logs` database table.
