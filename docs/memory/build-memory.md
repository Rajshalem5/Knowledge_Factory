# Knowledge Factory Build Memory

## What Built
- SaaS frontend → AI intern hiring platform
- React + TypeScript + Vite + Tailwind CSS
- Path: `app/`

## Design System = "Digital Curator"
- Navy primary: `#063342`
- Teal accent: `#006a62`
- Teal light: `#6cf5e6`
- Surface: `#f9f9ff` → `#eff3ff` → `#ffffff`
- Dark mode: `#0e1419` → `#141c24` → `#1a2330`
- Font: Inter only
- Display tracking: `-0.02em`
- Label tracking: `0.05em`

## Design Rules Applied
- No-Line Rule → no 1px borders ever
- Tonal surfaces → bg-layer shifts define edges
- Glassmorphism → modals = `backdrop-blur: 16px`
- Gradient CTAs → `135deg, #001d28 → #063342`
- Ghost shadow → `0px 12px 32px rgba(18,28,42,0.06)`
- No drop shadows on cards
- Elevation = lightness, not shadow

## 5 Roles
1. Candidate → glass top-nav
2. HR → navy sidebar
3. Interviewer → navy sidebar
4. Admin → navy sidebar
5. SuperAdmin → navy sidebar

## 10 Pages
1. `/` → Landing
2. `/login` → Login
3. `/register` → Register
4. `/verify-otp` → OTP
5. `/forgot-password` → Forgot
6. `/portal` → Candidate portal + progress pipeline
7. `/assessment` → Split-screen code editor
8. `/dashboard` → HR funnel + table
9. `/candidates/:id` → Detail with tabs
10. `/interview` → Interviewer feedback
11. `/selection` → Toggle select/reject
12. `/analytics` → Charts + stats
13. `/superadmin` → Org + user management

## Components Built
- UI: Button, Card, Input, Badge, Select, Toggle, Modal, Tabs, DataTable, ProgressPipeline, States
- Charts: StatCard, FunnelChart, BarChart
- Assessment: Timer, ProblemPanel, CodeEditor, TestOutput
- Layout: Sidebar, Header, AppShell, CandidateNav

## Key Patterns
- Pipeline = segmented bar (not dots/lines) + pulse animation
- Tables = no dividers, alternating row fills
- Cards = `bg-layer2` + `ghost-shadow` + `rounded-md`
- Labels = `text-tertiary uppercase tracking-architectural`
- Headings = `text-on-surface tracking-tight-display`

## API Layer
- Client: `src/api/client.ts`
- Auth: `src/api/auth.ts`
- Candidates: `src/api/candidates.ts`
- Assessment: `src/api/assessment.ts`
- Analytics: `src/api/analytics.ts`

## Hooks
- `useAuth` → AuthContext
- `useCandidates`, `useCandidate`, `useMyCandidateProfile`, `useUpdateCandidateStatus`
- `useAssessment`, `useActiveAssessments`, `useStartAssessment`, `useSubmitSection`, `useSubmitFeedback`
- `useFunnelData`, `useAnalytics`, `useOrganizations`

## Contexts
- AuthContext → login, register, logout, user state, token
- ThemeContext → dark/light toggle, localStorage persist

## Route Protection
- ProtectedRoute → checks role vs allowedRoles
- `canAccessRoute()` → per-role route whitelist
- Auto-redirect → role → ROLE_HOME_ROUTES

## Build Status
- `tsc --noEmit` = 0 errors
- `vite build` = 349KB JS + 37KB CSS
- Build time = 450ms

## Run
```
cd app
npm run dev
```

## Dependencies
- react-router-dom
- @tanstack/react-query
- lucide-react
- clsx
- tailwindcss + @tailwindcss/vite
