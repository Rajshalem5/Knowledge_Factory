# Project Structure Documentation

## SECTION 2 – PROJECT STRUCTURE

```text
/
├── app/                  # Frontend Application
│   ├── public/           # Static assets
│   ├── src/              # React Source Code
│   │   ├── api/          # API Client integration layer
│   │   ├── components/   # Reusable UI components
│   │   ├── contexts/     # React Contexts (Auth, etc.)
│   │   ├── hooks/        # Custom React Hooks
│   │   ├── pages/        # Page-level components
│   │   ├── routes/       # Route definitions & protection
│   │   ├── services/     # Frontend business logic
│   │   ├── types/        # TypeScript interfaces
│   │   └── utils/        # Helper functions
│   ├── package.json      # NPM dependencies
│   └── vite.config.ts    # Vite build configuration
│
├── backend/              # Core API Backend
│   ├── alembic/          # Database migrations
│   ├── app/              # FastAPI Source Code
│   │   ├── core/         # Core logic (security, enums, config)
│   │   ├── features/     # Feature modules (Domain Driven Design)
│   │   ├── middleware/   # Custom middlewares
│   │   ├── websockets/   # WebSocket handlers
│   │   ├── main.py       # FastAPI application entrypoint
│   │   └── database.py   # Database connection and session management
│   ├── scripts/          # Utility scripts (seed, test, inspect)
│   ├── tests/            # Pytest test suite
│   ├── requirements.txt  # Python dependencies
│   └── alembic.ini       # Alembic configuration
│
├── audi_video/           # AI Proctoring Microservice
│   ├── app/              # FastAPI Source Code for AI processing
│   ├── models/           # Pre-trained ML models (YOLO, etc.)
│   ├── tests/            # Test suite
│   └── requirements.txt  # Python dependencies
│
├── uploads/              # Local storage for uploaded resumes/IDs
├── screenshots/          # Local storage for proctoring evidence
└── docs/                 # Project documentation
```

---

## SECTION 3 – FRONTEND DOCUMENTATION

**Framework:** React + TypeScript + Vite

### Architecture Overview
The frontend is a classic Single Page Application (SPA). It uses React Router for navigation, Context API for global state (like Authentication), and a centralized API client for backend communication.

### Key Directories
*   **`/api`**: Contains isolated files for each backend module (e.g., `candidates.ts`, `auth.ts`). They utilize a core `client.ts` which handles auth tokens, auto-refresh via cookies, and global error handling.
*   **`/pages`**: Divided by user roles (`candidate`, `hr`, `interviewer`, `admin`, `super_admin`).
*   **`/components`**: Reusable UI blocks (buttons, tables, modals).

### Route Mapping

| Route | Component | Purpose |
| :--- | :--- | :--- |
| `/login` | `Login.tsx` | User & Candidate authentication |
| `/register` | `Register.tsx` | Candidate registration |
| `/portal` | `Portal.tsx` | Candidate dashboard |
| `/assessment` | `Assessment.tsx` | Test taking interface |
| `/dashboard` | `Dashboard.tsx` | HR operational overview |
| `/candidates` | `CandidatesList.tsx` | View & filter applicants |
| `/candidates/:id` | `CandidateDetail.tsx` | Detailed candidate view |
| `/interview` | `InterviewPanel.tsx` | Interviewer workspace |
| `/selection` | `SelectionPanel.tsx` | Final HR decisions |
| `/analytics` | `AnalyticsDashboard.tsx` | System metrics |
| `/admin/cycle-config` | `CycleConfig.tsx` | Hiring cycle management |

---

## SECTION 4 – BACKEND DOCUMENTATION

**Framework:** FastAPI (Python)

### Architecture Overview
The backend follows a Feature-Based (Domain Driven Design) directory structure. Each feature contains its own models, schemas, service layer, and router.

### Module Map

| Module | Purpose | Key Models |
| :--- | :--- | :--- |
| **Auth** | JWT generation, verification, and user management. | `User` |
| **Candidates** | Candidate profiles, bulk uploads, AI resume parsing. | `Candidate` |
| **Assessments** | Test state management, scoring, and submission tracking. | `Assessment`, `Submission`, `Score` |
| **Hiring Cycles** | Defines rules, eligibility, and phases for a hiring drive. | `HiringCycle` |
| **Proctoring** | WebSockets for live monitoring, event logging, risk scoring. | `ProctoringSession`, `ProctoringEvent` |
| **Interviews** | Capturing manual feedback from human interviewers. | `InterviewFeedback` |
| **Selection** | Final ranking and status updates for hiring. | N/A (Updates `Candidate`) |
| **Code Execution** | Interface to the Piston engine for secure evaluation. | N/A |
| **Analytics** | Data aggregation for dashboards and funnels. | N/A |
| **Audit** | Tracking administrative actions for compliance. | `AuditLog` |

### Core Concepts
*   **Dependency Injection:** Extensively used for database sessions (`get_db`) and role-based access control (`require_role`).
*   **Services:** Business logic is decoupled from routes into `service.py` files to ensure reusability and testability.
*   **Schemas:** Pydantic models handle all request validation and response serialization.
