# File Structure Map

```
app/src/
├── index.css              → Design system + Tailwind theme
├── main.tsx               → BrowserRouter + QueryClient + AuthProvider + ThemeProvider
├── App.tsx                → All routes wired
│
├── api/
│   ├── client.ts          → Base fetch wrapper + token auth
│   ├── auth.ts            → register, login, verifyOtp, forgotPassword, resetPassword, getMe
│   ├── candidates.ts      → getAll, getById, getMe, updateStatus, bulkUpload
│   ├── assessment.ts      → start, submitSection, getAssessment, getActiveAssessments, submitFeedback
│   └── analytics.ts       → getFunnel, getAnalytics, getOrganizations, updateOrganization
│
├── contexts/
│   ├── AuthContext.tsx     → user, token, login, register, logout, role
│   └── ThemeContext.tsx    → theme, toggleTheme, localStorage persist
│
├── hooks/
│   ├── useAuth.ts         → Re-export from AuthContext
│   ├── useCandidates.ts   → useCandidates, useCandidate, useMyCandidateProfile, useUpdateCandidateStatus
│   ├── useAssessment.ts   → useAssessment, useActiveAssessments, useStartAssessment, useSubmitSection, useSubmitFeedback
│   └── useAnalytics.ts    → useFunnelData, useAnalytics, useOrganizations
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx        → Navy sidebar for Admin/HR/Interviewer/SuperAdmin
│   │   ├── Header.tsx         → Top header with theme toggle
│   │   ├── AppShell.tsx       → Route-aware: sidebar for admin, glass nav for candidate
│   │   └── CandidateNav.tsx   → Glass top-navigation for candidates
│   ├── ui/
│   │   ├── Button.tsx         → primary=gradient-cta, secondary=ghost-border, ghost=transparent
│   │   ├── Card.tsx           → No-Line Rule, tonal surface lift
│   │   ├── Input.tsx          → Ghost ring, no solid border
│   │   ├── Badge.tsx          → Tinted background variants
│   │   ├── Select.tsx         → Ghost ring, no solid border
│   │   ├── Toggle.tsx         → secondary when on, surface-variant when off
│   │   ├── Modal.tsx          → Glassmorphism + ghost-shadow
│   │   ├── Tabs.tsx           → Tonal surface tabs, no border-bottom
│   │   ├── States.tsx         → LoadingState, ErrorState, EmptyState
│   │   ├── DataTable.tsx      → No dividers, alternating rows, all-caps headers
│   │   ├── ProgressPipeline.tsx → Segmented bar with pulse
│   │   └── index.ts           → Barrel export
│   ├── charts/
│   │   ├── StatCard.tsx       → Tonal card + secondary icon accent
│   │   ├── FunnelChart.tsx    → Horizontal bars, secondary/secondary-container
│   │   └── BarChart.tsx       → Horizontal bars, secondary
│   └── assessment/
│       ├── Timer.tsx          → Countdown, red when <5min
│       ├── ProblemPanel.tsx   → Problem description + test cases
│       ├── CodeEditor.tsx     → Line numbers + textarea, navy bg
│       └── TestOutput.tsx     → Pass/fail results, alternating rows
│
├── pages/
│   ├── Landing.tsx            → Hero + features + pipeline viz
│   ├── auth/
│   │   ├── Login.tsx          → Email + password
│   │   ├── Register.tsx       → Name + email + password + resume upload
│   │   ├── OTPVerification.tsx → 6-digit code input
│   │   └── ForgotPassword.tsx → Email → reset link sent
│   ├── candidate/
│   │   ├── Portal.tsx         → Profile + progress pipeline + assessments + scores
│   │   └── Assessment.tsx     → Split: problem | editor + output
│   ├── hr/
│   │   ├── Dashboard.tsx      → StatCards + funnel + candidate table
│   │   └── CandidateDetail.tsx → Tabs: scores, proctoring, interview, resume
│   ├── interviewer/
│   │   └── InterviewPanel.tsx → Candidate list + feedback form with sliders
│   ├── selection/
│   │   └── SelectionPanel.tsx → Toggle cards + bulk confirm
│   ├── analytics/
│   │   └── AnalyticsDashboard.tsx → StatCards + bar charts + funnel + violations
│   └── superadmin/
│       └── SuperAdminPanel.tsx → Org table + user table + overview cards
│
├── routes/
│   └── ProtectedRoute.tsx     → Role-based route guard
│
├── types/
│   └── index.ts               → Role, User, Candidate, Assessment, Problem, etc.
│
└── utils/
    ├── cn.ts                  → clsx wrapper
    └── roles.ts               → ROLE_LABELS, ROLE_HOME_ROUTES, STATUS_LABELS, STATUS_COLORS, canAccessRoute
```
