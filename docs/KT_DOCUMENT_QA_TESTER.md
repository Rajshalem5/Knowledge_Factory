# Knowledge Factory — Complete QA Testing Guide

## For Freelance Manual QA Tester

> **IMPORTANT**: This document is written in plain English. No code, no technical jargon. If anything is unclear, read the section again — it should answer your question. If it doesn't, flag it in your bug report.

---

## How to Use This Document

This is your complete guide to testing the Knowledge Factory web application. Work through it section by section. Start with Section 1 to understand what the app does. Then read your test credentials in Section 9, log in to each role in Section 2, and begin testing.

**Estimated total testing time: 6-8 hours** (split across multiple sessions)

---

# SECTION 1 — PROJECT OVERVIEW

## What is Knowledge Factory?

Knowledge Factory is a web-based hiring platform. It helps companies find and select intern candidates — college students applying for internships. The platform automates the entire process from application to final selection.

**The problem it solves:** When thousands of students apply for internships, it's impossible for HR teams to review each application manually. Knowledge Factory automates the screening, testing, and tracking so HR can focus on the best candidates.

## Who Uses It? (5 Roles)

**1. Candidate (Student applying for internship)**
This is a college student. They visit the website, create an account with their details (name, email, college, grades), upload their resume, and then take online coding tests. They can log in to see their application status — whether they are shortlisted, getting assessed, or selected.

**2. HR Manager (Recruitment person)**
This is someone from the company's HR team. They see a dashboard of all candidates, can run an automatic screening (which checks eligibility based on grades/branch), view detailed profiles of each candidate, download data as a spreadsheet, and decide who moves forward in the hiring process.

**3. Interviewer (Technical evaluator)**
This is a senior engineer or technical lead. They log in to see candidates who have passed the assessments. They review each candidate's scores and submit feedback (technical score, communication score, and a recommendation to select, hold, or reject).

**4. Admin (System administrator)**
This is a power user with access to everything HR can do, plus the interview panel and some system tools like audit logs and database export.

**5. Super Admin (Platform owner)**
This is the top-level administrator. They can see all users in the system, view their roles and statuses, and get an overview of the entire hiring pipeline.

## The Overall Flow (Start to Finish)

1. A candidate goes to the website and creates an account (fills in name, email, college, branch, grades, uploads resume).
2. The candidate is now in "Applied" status.
3. HR logs in and runs "Screening" — the system checks each candidate's eligibility (CGPA above minimum, etc.).
4. Eligible candidates move to "Round 1 Passed" status.
5. The candidate logs in and sees they are eligible. They click "Start Assessment" to begin a coding test.
6. The candidate solves coding problems in an online editor. They can run their code and submit it.
7. When the candidate completes the assessment, their status advances.
8. The candidate may need to complete Round 2 and Round 3 assessments.
9. After assessments, an interviewer reviews the candidate and submits feedback.
10. HR makes the final decision — Select or Reject.

## Live URL and How to Access

The application is accessible via a public ngrok URL (a temporary tunnel that exposes the local development server to the internet):

**Live URL:** https://ila-sturdiest-oversentimentally.ngrok-free.dev

You open this URL in Google Chrome on your laptop, and it loads the Knowledge Factory website.

> NOTE: ngrok URLs change when the tunnel is restarted. If the URL above does not work, contact the project owner for the current URL.

> IMPORTANT: The backend API documentation is also accessible at https://ila-sturdiest-oversentimentally.ngrok-free.dev/docs (Swagger UI). This is a debug feature — the tester can use it to explore API endpoints, but it is NOT part of normal user experience.

---

# SECTION 2 — ALL 5 ROLES (In Detail)

---

## ROLE 1: Candidate (Intern Applicant)

**Who is this person?** A college student who wants an internship. Let's call them Ravi. Ravi is in his final year of engineering, has a CGPA of 8.2, studies Computer Science at MIT, and knows Python.

**What can they do in the system?**
- Create a new account (register) with their name, email, password, college, branch, CGPA, graduation year, preferred programming language, and optional resume upload.
- Log in to see their personal portal.
- View their application progress — what stage they are at in the hiring pipeline.
- Start and take coding assessments (Round 2 and Round 3).
- See their past test scores.
- See if they have been selected or rejected.

**What can they NOT do?**
- Cannot see other candidates' data.
- Cannot see the HR dashboard or analytics.
- Cannot see the interview panel.
- Cannot change their role.
- Cannot view admin or super admin pages.

**What pages do they see after login?**
- /portal — Their personal dashboard showing profile, application progress, active assessments, past scores, and next step.
- /assessment — The coding assessment page where they solve problems (split-screen: left side shows the problem, right side has a code editor).

**Typical day-to-day workflow:**
1. Log in to https://....ngrok-free.dev
2. Click "Sign In" and enter email + password.
3. Land on the Portal page.
4. Check their application status (Applied → Eligible, etc.).
5. If eligible, click "Start Assessment" to begin the coding test.
6. On the assessment page, generate a coding question (or use the pre-loaded one).
7. Write code in the editor, run it to test, then submit.
8. Click "Complete & Advance" when done.
9. Log out.

**What does success look like?**
- Can register successfully.
- Can log in and see their portal.
- Can start an assessment.
- Can write code, run it, and see output.
- Can submit code and see test results.
- Can complete the assessment and advance to the next stage.
- Sees "Congratulations! You have been selected." if selected.

---

## ROLE 2: HR Manager (Recruiter)

**Who is this person?** Priya works in the HR department of a tech company. She is responsible for finding and shortlisting intern candidates. She uses this platform to manage hundreds of applicants.

**What can they do in the system?**
- View a dashboard with pipeline statistics (total candidates, screening pass rates, etc.).
- See a table of all candidates with their details (name, college, branch, CGPA, language, status).
- Search and filter candidates by name, college, branch, CGPA range, language, status, date range, and many other fields.
- Run "Screening" — automatically check candidate eligibility.
- Click on any candidate to see their full profile and scores.
- Manually mark candidates as "Selected" or "Rejected".
- Download candidate data as a CSV file (spreadsheet).
- View the Analytics Dashboard with charts and funnel data.
- View the Final Selection Panel to make batch selection decisions.
- View the Jobs/Hiring Cycles page.
- Access their Settings page.

**What can they NOT do?**
- Cannot take assessments (that's for candidates).
- Cannot submit interview feedback (that's for interviewers).
- Cannot see the Super Admin panel.
- Cannot manage system users.

**What pages do they see after login?**
- /dashboard — HR Dashboard with stats, filters, and candidate table.
- /candidates — Same as /dashboard (just a different route).
- /candidates/:id — Detailed view of a single candidate.
- /selection — Final Selection Panel.
- /analytics — Analytics Dashboard with charts.
- /settings — Account settings.
- /jobs — Job management (create jobs, generate questions).

**Typical day-to-day workflow:**
1. Log in to https://....ngrok-free.dev
2. Click "Sign In" and enter HR credentials.
3. Land on the Dashboard. See pipeline stats at the top.
4. Review new candidates in the table.
5. Use filters to narrow down candidates by branch (e.g., "CSE") or CGPA.
6. Click "Run Screening" to automatically check eligibility.
7. See the screening result (how many passed/rejected).
8. Click on a candidate's name to view their full profile.
9. On the candidate detail page, review scores and click "Select" or "Reject".
10. Go to Analytics to view hiring funnel and charts.
11. Go to Selection panel to make final batch decisions.
12. Download CSV to export data to Excel.

**What does success look like?**
- Dashboard loads with correct pipeline numbers.
- Candidate table shows real data with pagination.
- Filters work and narrow down results correctly.
- Screening runs and shows pass/fail counts.
- Candidate detail page shows correct information.
- Status updates (Select/Reject) work and persist.
- CSV downloads with correct data.
- Analytics shows real data (or at least doesn't crash).
- Charts render properly.

---

## ROLE 3: Interviewer (Technical Evaluator)

**Who is this person?** Ankita is a senior software engineer at the company. She interviews candidates who have passed the coding assessments. She rates them on technical ability and communication.

**What can they do in the system?**
- See a list of candidates assigned to them (currently shows all candidates in "round3" status).
- Click on a candidate to see their details and past scores.
- Fill out an interview feedback form with:
  - Technical score (0-10 slider)
  - Communication score (0-10 slider)
  - Recommendation: Select / Hold / Reject
  - Free-text notes
- Submit feedback, which persists.

**What can they NOT do?**
- Cannot see the HR dashboard or analytics.
- Cannot view assessment page.
- Cannot change candidate status directly.
- Cannot access admin or super admin pages.

**What pages do they see after login?**
- /interview — Interview Panel with two sections: candidate list on the left, feedback form on the right.

**Typical day-to-day workflow:**
1. Log in to https://....ngrok-free.dev
2. Enter interviewer credentials.
3. Land on the Interview Panel.
4. See a list of candidates on the left.
5. Click on a candidate to select them.
6. View their basic info and assessment scores.
7. Adjust the technical score slider (0-10).
8. Adjust the communication score slider (0-10).
9. Choose Select / Hold / Reject.
10. Type interview notes.
11. Click "Submit Feedback".
12. See a success confirmation.
13. Move to the next candidate.

**What does success look like?**
- Candidate list loads with names and colleges.
- Clicking a candidate shows their details.
- Score sliders work and display the current value.
- Recommendation buttons toggle correctly.
- Submit Feedback button works and shows confirmation.
- Feedback persists (re-opening the candidate shows existing feedback — currently not implemented, so a simple success message is enough).

---

## ROLE 4: Admin (System Administrator)

**Who is this person?** Raj is the system administrator. He has all the HR powers plus some extra system tools. He can step in if the HR person is unavailable.

**What can they do in the system?**
- Everything an HR Manager can do (dashboard, candidates, filters, screening, CSV download).
- Everything an Interviewer can do (interview panel, submit feedback).
- View the Admin Dashboard with:
  - Audit Logs — a log of all actions performed in the system.
  - Database Export — download all data as a JSON file.

**What can they NOT do?**
- Cannot take assessments (candidate role only).
- Cannot access Super Admin features (managing users).

**What pages do they see after login?**
- /dashboard — Same HR Dashboard.
- /candidates — Same candidate list.
- /candidates/:id — Candidate detail.
- /selection — Selection panel.
- /analytics — Analytics.
- /interview — Interview panel.
- /admin — Admin Dashboard (Audit Logs + DB Export).
- /settings — Settings.

**Typical day-to-day workflow:**
Similar to HR + Interviewer, plus occasionally checking audit logs and doing database exports.

**What does success look like?**
- Has access to HR dashboard, candidate list, selection panel, analytics, AND interview panel.
- /admin page loads and shows Audit Logs tab.
- Clicking Audit Logs tab loads log entries (may be empty if no actions logged yet).
- Database Export button works and downloads a JSON file.

---

## ROLE 5: Super Admin (Platform Owner)

**Who is this person?** The company's platform owner (or the project creator). They have the highest level of access. They can see everything across the entire platform.

**What can they do in the system?**
- See a list of ALL users in the system with their roles and statuses.
- View statistics: total users, active users, number of roles.
- Switch between "Users & Roles" view and "Pipeline Summary" view.
- Everything an Admin can see (dashboard, candidates, analytics, selection).

**What can they NOT do?**
- Cannot take assessments (candidate role only).
- (There is very little restricted from this role.)

**What pages do they see after login?**
- /superadmin — Super Admin Panel with user table and stats.
- /dashboard — HR Dashboard.
- /candidates — Candidate list.
- /candidates/:id — Candidate detail.
- /selection — Selection panel.
- /analytics — Analytics.
- /admin — Admin dashboard.
- /settings — Settings.

**Typical day-to-day workflow:**
1. Log in with Super Admin credentials.
2. Land on Super Admin panel.
3. See the overview cards (Total Users, Active Users, Roles).
4. View the Users & Roles table showing all system users.
5. Optionally switch to Pipeline Summary tab.
6. Can navigate to other sections as needed.

**What does success look like?**
- Super Admin panel loads with stats cards showing real numbers.
- User table populates with all system users.
- User roles, statuses, and creation dates are visible.
- Tab switching works between Users and Pipeline Summary.

---

# SECTION 3 — EVERY PAGE & SCREEN

## Page 1: Landing Page

**URL:** `/` (https://....ngrok-free.dev/)

**Purpose:** First page visitors see. It describes what Knowledge Factory is and lets people log in or register.

**What the tester expects to see:**
- A navigation bar at the top with the "Knowledge Factory" logo, a dark/light theme toggle button, and two buttons: "Login" and "Apply Now".
- A hero section with the text "Hire smarter. Evaluate faster." and a description paragraph.
- Two buttons: "Start Application" and "Sign In".
- A "Features" section with 4 feature cards: "AI-Powered Assessments", "Proctored Evaluations", "Bias-Free Selection", "End-to-End Pipeline".
- A "Hiring Pipeline" visualization showing 7 steps in circles: Applied → Eligible → Round 1 → Round 2 → Round 3 → Interview → Selected.
- A footer.
- Dark-themed, modern design.

**What each button/action does:**
- "Login" / "Sign In" → Goes to /login page
- "Apply Now" / "Start Application" → Goes to /register page
- Theme toggle → Switches between dark and light mode
- "Dashboard" (when logged in) → Goes to the logged-in user's home page

**Who can access:** Everyone (no login required)

**What if unauthorized tries to access:** N/A — this is a public page

---

## Page 2: Login Page

**URL:** `/login`

**Purpose:** Allow existing users to sign in.

**What the tester expects to see:**
- Page title: "Welcome back"
- Subtitle: "Sign in to your account"
- Email input field with placeholder "you@example.com"
- Password input field with placeholder "Enter your password"
- "Forgot password?" link (top-right above the sign-in button)
- "Sign In" button
- Below the form: "Don't have an account? Apply now" link
- Error messages in a red box if login fails
- Knowledge Factory logo at the top

**What each button/action does:**
- "Sign In" → Submits the form. If successful, redirects to the user's home page based on their role. If failed, shows an error message.
- "Forgot password?" → Goes to /forgot-password page
- "Apply now" → Goes to /register page

**Who can access:** Everyone

**What if unauthorized tries to access:** N/A — public page

---

## Page 3: Register Page

**URL:** `/register`

**Purpose:** Allow new candidates to create an account and apply.

**What the tester expects to see:**
- Page title: "Create your account"
- Subtitle: "Start your application"
- A back arrow button (top-left, goes to home page)
- Form fields (all marked required except Resume):
  - Full Name (text input, placeholder "John Doe")
  - Email (email input, placeholder "you@example.com")
  - Password (password input, placeholder "Create a password (min 8 characters)")
  - College (text input, placeholder "Your college name")
  - Branch (text input, placeholder "e.g., Computer Science")
  - CGPA (number input, placeholder "e.g., 8.5", 0-10 range)
  - Passed Out Year (number input, placeholder "e.g., 2024", 2000-2030 range)
  - Resume upload (drag-and-drop area, accepts .pdf, .doc, .docx, max 5MB) — optional
  - Preferred Language (dropdown: Python, JavaScript, Java, C++, C)
- "Create Account" button
- "Already have an account? Sign in" link

**What each button/action does:**
- Back arrow → Goes to Landing page (/)
- "Create Account" → Validates form, submits registration. If successful, redirects to /portal. If failed, shows error.
- Upload area → Opens file picker for resume.
- "Remove" (on uploaded file) → Clears the selected resume file.
- "Sign in" → Goes to /login

**Who can access:** Everyone

**What if unauthorized tries to access:** N/A — public page

---

## Page 4: OTP Verification Page

**URL:** `/verify-otp`

**Purpose:** Verify the candidate's email address using a one-time code sent to their email.

**What the tester expects to see:**
- Page title: "Verify your email"
- Subtitle showing the email address (or "Enter the verification code sent to your email")
- Input field: "Verification Code" (6-digit, numeric)
- "Verify" button
- "Resend code" link below the button

**What each button/action does:**
- "Verify" → Submits the OTP code for verification. If successful, redirects to /portal. If failed, shows error.
- "Resend code" → Sends a new OTP code to the email (may not work — see Known Issues).

**Who can access:** Anyone who just registered.

**What if unauthorized tries to access:** Redirects to login page if user is not in the middle of registration flow.

---

## Page 5: Forgot Password Page

**URL:** `/forgot-password`

**Purpose:** Allow users to request a password reset email.

**What the tester expects to see:**
- Page title: "Reset password"
- Subtitle: "Enter your email and we'll send you a reset link."
- Email input field
- "Send Reset Link" button
- "Back to sign in" link

**After submitting:**
- Page changes to "Check your email" with the email address shown and a "Back to sign in" link.

**What each button/action does:**
- "Send Reset Link" → Submits the email. The page changes to show "Check your email" message (the email will NOT actually be sent — see Known Issues).
- "Back to sign in" → Goes to /login

**Who can access:** Everyone

**What if unauthorized tries to access:** N/A — public page

---

## Page 6: Candidate Portal

**URL:** `/portal`

**Purpose:** The candidate's personal dashboard. Shows their application status, progress in the pipeline, active assessments, and past results.

**What the tester expects to see:**
- Sidebar navigation (if using AppShell layout) with the candidate's name/initials.
- **Profile Card:**
  - Candidate's name and email
  - Status badge (Applied, Eligible, Round 1, etc.)
  - College, Branch, CGPA in a 3-column grid
- **Application Progress Card:**
  - A visual pipeline showing steps: Applied → Eligible → Round 1 → Round 2 → Round 3 → Interview
  - The current step is highlighted
  - If selected: "Congratulations! You have been selected." in green
  - If rejected: "Your application was not selected this time." in red
- **Active Assessments Card:**
  - Shows any active assessments with round number, time limit, and status (In Progress / Not Started / Completed)
  - Has a right-arrow button to go to the assessment
  - Only appears if there are active assessments
- **Past Results Card:**
  - Shows scores from completed rounds (if any)
  - Each round shown as a small card with score and maxScore
  - Only appears if scores exist
- **Next Step Section:**
  - Shows contextual guidance text based on current status
  - If eligible: Shows "Start Assessment" button
  - If assessment in progress: Shows "Continue Assessment" button
  - If passed round: Shows "Start Next Assessment" button

**What each button/action does:**
- "Start Assessment" → Starts a new assessment (Round 2) and navigates to /assessment
- "Start Next Assessment" → Starts Round 3 assessment and navigates to /assessment
- "Continue Assessment" → Navigates to /assessment to continue existing assessment
- Right-arrow on assessment card → Goes to /assessment
- Sidebar links → Navigate to different sections

**Who can access:** Candidates only

**What if unauthorized tries to access:** Redirects to login page or shows an error.

---

## Page 7: Assessment Page

**URL:** `/assessment`

**Purpose:** The coding test environment. Candidates solve programming problems here.

**What the tester expects to see:**
- **Header bar:**
  - Badge showing current Round (Round 2 or Round 3)
  - "Coding Assessment" title
  - Timer showing remaining time (starts at 60 minutes, counts down)
  - Three buttons: "Run", "Submit", "Complete & Advance"
- **Left panel (Problem):**
  - Input field for topic (placeholder: "Topic (e.g. binary search, graphs)")
  - Difficulty dropdown (Easy, Medium, Hard)
  - "Generate Question" button — generates an AI-powered question
  - Problem description area:
    - If no question loaded: Shows a refresh icon and "Generate a question to begin"
    - If question loaded: Shows difficulty badge, problem title, description text
  - Example Test Cases section showing input and expected output
  - "4 hidden test cases used for final scoring" notice
- **Right panel (Code Editor & Output):**
  - "Solution" label
  - Language selector dropdown (Python 3, Java, C++) with version labels
  - Code editor (code typing area) with starter code or boilerplate
  - Custom Input text area (for typing test input)
  - Output panel at bottom showing:
    - Run results (status + output)
    - Evaluation results (passed/total tests, score percentage, individual test results with checkmarks or X's)
    - Or "Run your code or submit to see results" placeholder

**What each button/action does:**
- "Generate Question" → Calls AI to generate a coding problem based on topic and difficulty. Loads it into the problem panel.
- "Run" → Executes the code with the custom input. Shows output in the bottom panel.
- "Submit" → Submits the code for evaluation against all test cases. Records the submission. Shows test results (pass/fail per test case, score percentage).
- "Complete & Advance" → Marks the assessment as complete, advances the candidate to the next round. Opens a confirmation dialog first. Only enabled after at least one successful submission.
- Language dropdown → Changes the programming language. Swaps boilerplate code.
- Topic input / Difficulty dropdown → Sets parameters for question generation.

**Who can access:** Candidates only (who have an active assessment)

**What if unauthorized tries to access:** Redirects to login or shows "Access Denied".

---

## Page 8: HR Dashboard

**URL:** `/dashboard`

**Purpose:** The main HR command center. Shows pipeline statistics and the full candidate list with search/filter/sort.

**What the tester expects to see:**
- **Sidebar navigation** with links to Dashboard, Jobs, Candidates, Selection, Analytics, Settings.
- **Pipeline Stats Cards** (grid of small cards):
  - Total Candidates (with people icon)
  - Applied → Passed (showing ROUND1_PASSED / APPLIED count, with "Run Screening" button)
  - R2 In Progress count
  - R3 In Progress count
  - Average CGPA
  - Completion Rate (percentage, with completed/total count)
  - Interview Scheduled count
  - Selected count
- **Funnel Stage Aggregates** (4 more cards):
  - Eligible (passed screening)
  - In Assessment (R2 + R3 candidates)
  - Interviewed (scheduled + completed)
  - Selected (offers extended)
- **Filter Section** (collapsible):
  - Toggle button "Pipeline Filters" to expand/collapse
  - "Reset All Filters" button
  - When expanded, shows filter inputs:
    - Branch Filter (text)
    - College Filter (text)
    - Passed Out Year (number)
    - Language Choice (select)
    - CGPA Min / Max (number)
    - Has Resume / Has Govt ID / Has Phone (select: yes/no/any)
    - Has Assessment / Has Interview Feedback (select)
    - Created After / Before (date)
    - Updated After / Before (date)
    - Assessment Status (text)
    - Min / Max Score (number)
    - Email Verified (select)
    - Phone / Email / Name filters (text)
    - Target Statuses (text)
- **Screening Results** message when screening completes ("Screened: X passed, Y rejected")
- **Candidate Table** with columns:
  - Name (clickable)
  - College
  - Branch
  - Docs (icons showing if resume, govt ID, phone exist)
  - Passed Out Year
  - Language
  - Updated (relative time: "5m ago", "2h ago", etc.)
  - CGPA
  - Status (colored badge: Applied, Eligible, Selected, Rejected, etc.)
- **Pagination** at the bottom (page numbers, previous/next)
- **CSV Download** button
- **Sort** — clicking column headers sorts the table

**What each button/action does:**
- "Run Screening" → Triggers automatic screening. Shows "Running..." while processing, then shows pass/fail count.
- Filter inputs → Type or select to filter the candidate list. Table updates automatically.
- "Reset All Filters" → Clears all filter fields.
- "Pipeline Filters" toggle → Shows/hides the filter section.
- Candidate name → Click to go to candidate detail page (/candidates/:id)
- Column headers → Click to sort asc/desc
- CSV Download → Downloads a CSV file with the current candidate data.
- Pagination buttons → Navigate between pages.

**Who can access:** HR, Admin, Super Admin

**What if unauthorized tries to access:** Interviewers or Candidates see access denied.

---

## Page 9: Candidate List (same as Dashboard, different route)

**URL:** `/candidates`

**Purpose:** Same as /dashboard — just shows the dashboard component. Exists as an alternate route.

**What the tester expects to see:** Same as /dashboard.

**Who can access:** HR, Admin, Interviewer, Super Admin (broader access than /dashboard)

**Note:** Interviewers can access /candidates but NOT /dashboard. For interviewers, this shows the HR Dashboard component — they will see pipeline stats and the candidate table.

---

## Page 10: Candidate Detail Page

**URL:** `/candidates/:id` (e.g., /candidates/abc-123-def)

**Purpose:** View full details of a single candidate.

**What the tester expects to see:**
- "Back" button (arrow with text) at top
- **Candidate Profile Card:**
  - Avatar circle with first letter of name
  - Full name and email
  - College, Branch, CGPA in a row
  - Status badge (color-coded)
  - "Select" button (green/primary)
  - "Reject" button (red)
- **Tabs section with:**
  - **Scores tab** (default):
    - List of assessment scores by round (if any)
    - Each shows round number, score, maxScore
    - Or "No scores yet." if empty
  - **Proctoring tab** (if proctoring flags exist):
    - List of proctoring flags with details
    - Or "No flags recorded." if empty

**What each button/action does:**
- "Back" → Goes to the previous page (dashboard or candidate list)
- "Select" → Immediately marks candidate as Selected. Button may show loading state.
- "Reject" → Immediately marks candidate as Rejected.
- Tab click → Switches between Scores and Proctoring views.

**Who can access:** HR, Admin, Interviewer, Super Admin

**What if unauthorized tries to access:** Redirects to login or shows error.

---

## Page 11: Job Management (Hiring Cycles)

**URL:** `/jobs`

**Purpose:** Create and manage job postings / hiring cycles. Generate interview questions for specific jobs.

**What the tester expects to see:**
- **Stats cards:** Total Jobs, Active, Closed counts.
- **Job Creation Panel:** (appears when "New Job" is clicked):
  - Job title input
  - Job description textarea
  - Cancel and Create Job buttons
- **Job Table:**
  - Job Title column
  - Location column
  - Openings column
  - Status column (badge: OPEN or CLOSED)
  - Actions column: "Generate Questions" button + "Close" / "Reopen" button
- **Question Generation Modal:**
  - Question Topic input
  - Difficulty Level dropdown
  - Cancel and Generate Question buttons

**What each button/action does:**
- "New Job" → Shows the Create Job form.
- "Create Job" → Creates a new job posting. Form disappears on success.
- "Cancel" → Hides the create job form.
- "Generate Questions" (in table) → Opens the question generation modal for that job.
- "Close" → Changes job status to CLOSED.
- "Reopen" → Changes job status back to OPEN.
- "Generate Question" (in modal) → Generates an AI question for the job.

**Who can access:** HR, Admin, Super Admin (from sidebar)

**What if unauthorized tries to access:** Redirects or shows access denied.

---

## Page 12: Selection Panel

**URL:** `/selection`

**Purpose:** Final selection — HR can batch-select or reject candidates who have been interviewed.

**What the tester expects to see:**
- Page title: "Final Selection"
- Subtitle showing count: "X candidates ready for final decision"
- "Confirm All Decisions" button
- Grid of candidate cards (each showing):
  - Avatar circle with first letter of name
  - Candidate name
  - College name
  - Branch and CGPA
  - Assessment scores by round
  - Toggle switch (on = selected, off = rejected)
  - Status footer: "Select" (green) or "Reject" (red) based on toggle
- "No candidates ready for selection" message if list is empty

**What each button/action does:**
- Toggle switch → Flip between selected/rejected for each candidate.
- "Confirm All Decisions" → Applies all toggled decisions at once (selected → SELECTED, rejected → REJECTED).

**Who can access:** HR, Admin, Super Admin

**What if unauthorized tries to access:** Redirects or shows access denied.

---

## Page 13: Analytics Dashboard

**URL:** `/analytics`

**Purpose:** Visual charts and reports showing hiring pipeline metrics.

**What the tester expects to see:**
- **Overview Card:** Total Candidates (currently shows hardcoded "1,240")
- **Charts Grid (2 columns):**
  - **Pass Rate Per Round** — Bar chart showing pass rates for Round 1, 2, 3 (currently shows mock data: 75%, 60%, 45%)
  - **Hiring Funnel** — Funnel chart showing stages: applied → eligible → assessed → interviewed → selected (real database counts)
  - **College-wise Breakdown** — Bar chart showing candidate counts by college (shows empty/mock data)
  - **Branch-wise Performance** — Bar chart showing average scores by branch (shows empty/mock data)
- **Proctoring Violations** section (full width) showing violation counts by type (currently empty)

**Who can access:** HR, Admin, Super Admin

**What if unauthorized tries to access:** Redirects or shows access denied.

---

## Page 14: Interview Panel

**URL:** `/interview`

**Purpose:** Interviewers review candidate profiles and submit feedback.

**What the tester expects to see:**
- **Left panel: "Assigned Candidates"**
  - List of candidate items (name, college, branch badge)
  - Clickable — selecting one shows their details on the right
  - "No candidates assigned" if list is empty
- **Right panel:**
  - If no candidate selected: Icon + "Select a candidate to provide feedback"
  - If candidate selected:
    - Candidate info card (avatar, name, college/branch/CGPA)
    - Assessment scores (by round)
    - **Feedback form:**
      - Technical Score (slider 0-10 with number display)
      - Communication Score (slider 0-10 with number display)
      - Recommendation (3 toggle buttons: Select / Hold / Reject)
      - Notes (multi-line text area)
      - "Submit Feedback" button

**What each button/action does:**
- Candidate list item → Selects that candidate, shows their info and feedback form.
- Technical score slider → Adjusts score. Number updates live.
- Communication score slider → Adjusts score. Number updates live.
- Recommendation buttons → Toggle between Select / Hold / Reject.
- Notes textarea → Type interview notes.
- "Submit Feedback" → Submits the feedback form.

**Who can access:** Interviewer, Admin

**What if unauthorized tries to access:** HR sees access denied (HR cannot access /interview).

---

## Page 15: Super Admin Panel

**URL:** `/superadmin`

**Purpose:** Platform-wide overview showing all system users and their roles.

**What the tester expects to see:**
- **Overview Cards (3):** Total Users, Active Users, Roles (number of distinct roles)
- **Tab switcher:** "Users & Roles" | "Pipeline Summary"
- **Users & Roles Tab (default):**
  - "System Users" title
  - Table with columns:
    - Name (with avatar circle, email below name)
    - Role (badge: SUPERADMIN, ADMIN, HR, INTERVIEWER)
    - Status (badge: ACTIVE, INACTIVE, PENDING)
    - Created (date)
- **Pipeline Summary Tab:**
  - Shows a card directing to Analytics Dashboard for more details.

**Who can access:** Super Admin only

**What if unauthorized tries to access:** Shows an access denied message or redirects.

---

## Page 16: Admin Dashboard

**URL:** `/admin`

**Purpose:** System administration tools — audit logs and database export.

**What the tester expects to see:**
- Page title: "Admin Dashboard"
- Two tab buttons: "Audit Logs" | "Export DB"
- **Audit Logs Tab:**
  - Table with columns: Action, Entity, User, IP, Timestamp
  - Or "No audit logs yet." if empty
  - Clicking "Audit Logs" loads the logs
- **Export DB Tab:**
  - Description text
  - "Download DB Export" button
  - Status message ("Exporting...", "Export downloaded.", or error message)

**What each button/action does:**
- "Audit Logs" → Loads and displays audit log entries from the server.
- "Export DB" → Switches to export tab.
- "Download DB Export" → Downloads a JSON file with all database data.

**Who can access:** Admin, Super Admin

**What if unauthorized tries to access:** Redirects or shows access denied.

---

## Page 17: Settings Page

**URL:** `/settings`

**Purpose:** View account details and delete account.

**What the tester expects to see:**
- Page title: "Settings"
- **Account Section:** Shows Name, Email, Role
- **Danger Zone Section:**
  - Warning text: "Permanently delete your account..."
  - "Delete Account" button
  - After clicking Delete: Password input + "Confirm Delete" + "Cancel" buttons

**Who can access:** HR, Admin, Super Admin

**What if unauthorized tries to access:** Redirects.

---

## Page 18: Privacy & Terms Pages

**URL:** `/privacy` and `/terms`

**Purpose:** Legal information pages.

**What the tester expects to see:** Static pages with privacy policy and terms of service content.

**Who can access:** Everyone

---

# SECTION 4 — COMPLETE USER FLOWS (Step by Step)

---

## FLOW A: New Candidate Registers and Applies

Estimated time: 5 minutes

1. Open Chrome and go to https://....ngrok-free.dev
2. You see the Landing page. Click "Apply Now" (top-right) or "Start Application" (center).
3. You are on the Register page. Fill in:
   - Full Name: "QA Test Student"
   - Email: "qatest_student_2026@test.com"
   - Password: "TestPass123!" (minimum 8 characters)
   - College: "Test University"
   - Branch: "Computer Science"
   - CGPA: "8.5"
   - Passed Out Year: "2026"
   - Preferred Language: "Python"
   - Resume: Click the upload area, select a PDF file (optional — you can skip by not uploading).
4. Click "Create Account".
5. EXPECTED: You are redirected to /portal (or to OTP verification page if email verification is enabled).

---

## FLOW B: HR Runs Screening and Views Results

Estimated time: 5 minutes

1. Log in as HR (see test credentials in Section 9).
2. You are on the Dashboard (/dashboard).
3. Look at the top section — you see pipeline stats cards.
4. Find the "Applied → Passed" card. Note the numbers.
5. Click "Run Screening" (it's a small button in that card).
6. The button text changes to "Running..." briefly.
7. EXPECTED: After a few seconds, a green message appears: "Screened: X passed, Y rejected".
8. The pipeline stats numbers should update.
9. Scroll down to the candidate table.
10. The candidate table shows all candidates. If you just registered in Flow A, you should see "QA Test Student" in the table with status "Applied" (or "Eligible" if screening ran).

---

## FLOW C: Candidate Receives and Starts Assessment

Estimated time: 3 minutes

1. Log out of HR. Log in as the candidate you just registered (qatest_student_2026@test.com / TestPass123!).
2. You are on /portal.
3. Check your status badge — it should say "Applied" or "Eligible".
4. If it says "Applied":
   - Ask HR to run screening (Flow B), then refresh your portal page.
5. If it says "Eligible":
   - Look at the "Next Step" section at the bottom.
   - You should see "You are eligible! Start your assessment now."
   - Click "Start Assessment".
6. EXPECTED: You are redirected to /assessment.
7. The assessment page shows a split screen. Left side: "Generate a question to begin". Right side: code editor.

---

## FLOW D: Candidate Completes Assessment (Code Editor, Timer, Test Cases)

Estimated time: 10 minutes

1. You are on the Assessment page (/assessment).
2. **IMPORTANT: Check if a question is already loaded** (the assessment may have pre-loaded questions from the database).
   - If you see a problem description on the left, skip to step 6.
   - If you see "Generate a question to begin", continue to step 3.
3. Type a topic in the input field, e.g., "arrays" or "factorial".
4. Select difficulty "Easy".
5. Click "Generate Question".
   - EXPECTED: A question appears on the left with title, description, and example test cases.
   - NOTE: If generation fails (AI API key may not be configured), the page may show an error. This is a known issue.
6. If a question is loaded (either pre-loaded or generated), look at the code editor on the right.
7. Type some Python code in the editor. For example:
   ```
   def solve():
       return "hello"
   ```
8. In the "Custom Input" box below the editor, type some test input.
9. Click "Run".
   - EXPECTED: The output panel at the bottom shows the result (output or error).
10. Click "Submit".
    - EXPECTED: The bottom panel shows evaluation results: number of tests passed, score percentage, and individual test statuses (green checkmark = pass, red X = fail).
11. Click "Complete & Advance".
    - A confirmation dialog appears: "Submit and complete this assessment?"
    - Click "OK".
    - EXPECTED: You are redirected back to /portal.
12. On the portal page, your status should have advanced.

---

## FLOW E: HR Views Assessment Results and Moves Candidate Forward

Estimated time: 3 minutes

1. Log in as HR.
2. Go to /dashboard.
3. Find "QA Test Student" in the candidate table.
4. Click on their name.
5. You are on the Candidate Detail page (/candidates/:id).
6. Look at the "Scores" tab.
   - EXPECTED: You should see the assessment scores from the test the candidate completed.
   - (If scores show 0 or empty — this is a known issue.)
7. Click "Select" button to move the candidate forward, or click "Reject".
8. EXPECTED: The status badge updates. You see a brief loading state, then the badge changes.

---

## FLOW F: Interviewer Logs In, Reviews Candidate, Submits Feedback

Estimated time: 5 minutes

1. Log out. Log in as Interviewer (see Section 9).
2. You are on the Interview Panel (/interview).
3. On the left panel, you should see a list of candidates.
   - NOTE: Currently the system shows ALL candidates with "round3" status. If no candidates are in that status, the list will be empty.
4. If candidates are listed, click on one.
5. The right panel shows the candidate's details and scores.
6. Adjust the Technical Score slider (drag to a value like 7).
7. Adjust the Communication Score slider (drag to 8).
8. Click "Hold" for recommendation.
9. Type some notes: "Good technical skills, needs improvement in communication."
10. Click "Submit Feedback".
11. EXPECTED: A success message or loading indicator. The form may reset.
    - (NOTE: The feedback persists in the database. Refreshing the page should not lose it — though currently the UI may not show previously submitted feedback.)

---

## FLOW G: HR Makes Final Selection Decision

Estimated time: 3 minutes

1. Log in as HR.
2. Go to /selection.
3. You see a grid of candidates who have been interviewed (status = "interviewed" or later).
4. For each candidate, the toggle switch starts at their current status (on = selected, off = rejected).
5. Toggle switches as needed.
6. Click "Confirm All Decisions".
7. EXPECTED: The candidates' statuses are updated in the database. The page may refresh.

---

## FLOW H: Admin Manages Users

Estimated time: 5 minutes

1. Log in as Admin (see Section 9).
2. Go to /admin (type it in the browser address bar).
3. You see the Admin Dashboard.
4. Click "Audit Logs" tab.
   - EXPECTED: Some log entries load, or "No audit logs yet." appears.
5. Click "Export DB" tab.
6. Click "Download DB Export".
   - EXPECTED: A JSON file downloads to your computer.
7. Check that the JSON file contains data (open it in a text editor and verify it has content).

---

## FLOW I: Super Admin Views System Overview

Estimated time: 3 minutes

1. Log in as Super Admin (see Section 9).
2. You are redirected to /superadmin.
3. EXPECTED: You see 3 stat cards showing Total Users, Active Users, and number of Roles.
4. Below that, the Users & Roles table shows all users in the system.
5. Click "Pipeline Summary" tab.
   - EXPECTED: A message directing to Analytics Dashboard.

---

## FLOW J: HR Bulk Uploads Candidates via CSV

Estimated time: 5 minutes

1. Log in as HR.
2. Go to /dashboard.
3. Look for a "Bulk Upload" or "Upload Candidates" button/feature.
   - NOTE: This feature is NOT YET IMPLEMENTED. There is no UI for bulk upload on the HR dashboard. This flow cannot be tested.

---

## FLOW K: HR Uses Filters and Search on Candidate List

Estimated time: 8 minutes

1. Log in as HR.
2. Go to /dashboard.
3. At the top of the candidate table, find the search box.
4. Type a candidate's name (e.g., "QA Test").
   - EXPECTED: The table filters to show only candidates matching that name.
5. Clear the search. Click "Pipeline Filters" toggle.
6. A filter panel expands with many filter fields.
7. Try each filter:
   - Type "CSE" in Branch Filter → table updates
   - Type "Test University" in College Filter → table updates
   - Select a status from the Status dropdown → table updates
   - Set CGPA Min to "8.0" → table updates
   - Type a date in Created After (format: YYYY-MM-DD) → table updates
8. Click "Reset All Filters".
   - EXPECTED: All filters clear, table returns to full list.
9. Click column headers to sort (Name, College, CGPA, Status, etc.).
   - EXPECTED: Table sorts ascending on first click, descending on second click.
10. Click page numbers at the bottom to navigate between pages.

---

## FLOW L: HR Views Analytics Dashboard

Estimated time: 5 minutes

1. Log in as HR.
2. In the sidebar, click "Analytics".
3. You are on /analytics.
4. EXPECTED: The page loads with:
   - A card showing "Total Candidates: 1,240" (this is a mock number)
   - Pass Rate Per Round bar chart (showing 3 bars: Round 1 at 75%, Round 2 at 60%, Round 3 at 45%)
   - Hiring Funnel chart (showing real counts from database: applied → eligible → assessed → interviewed → selected)
   - College-wise Breakdown bar chart (empty — no data)
   - Branch-wise Performance bar chart (empty — no data)
   - Proctoring Violations section (empty — no data)
5. NOTE: The 1,240 number is fake/hardcoded. The pass rate values are fake/mock. The college and branch charts are empty. Only the Hiring Funnel shows real data.

---

# SECTION 5 — WHAT GOOD LOOKS LIKE (Expected Behavior)

## Registration
- **Before:** Register form is blank.
- **After clicking Create Account:** Loading spinner on button. Then redirects to /portal.
- **Success confirmation:** You land on /portal with your name and "Applied" status.
- **Time:** 2-5 seconds.

## Login
- **Before:** Login form with email and password fields.
- **After clicking Sign In:** Loading spinner. Then redirects to role-specific home page.
- **Success confirmation:** You land on the correct page for your role.
- **Time:** 1-3 seconds.

## Run Screening (HR)
- **Before:** Pipeline stats show current counts. "Run Screening" button is visible.
- **After clicking Run Screening:** Button shows "Running..." briefly.
- **Success confirmation:** Green message appears: "Screened: X passed, Y rejected". Stats numbers update.
- **Time:** 3-10 seconds (depends on number of candidates).

## Candidate Starts Assessment
- **Before:** Portal page shows "You are eligible! Start your assessment now."
- **After clicking Start Assessment:** Button shows "Starting..." briefly.
- **Success confirmation:** Redirected to /assessment page.
- **Time:** 2-5 seconds.

## Candidate Runs Code
- **Before:** Code editor shows code. Custom input has some text.
- **After clicking Run:** Button shows "Running..." briefly.
- **Success confirmation:** Output panel shows execution result (output text or error).
- **Time:** 1-5 seconds (depends on code execution server).

## Candidate Submits Code
- **Before:** Code is in the editor.
- **After clicking Submit:** Button shows loading state.
- **Success confirmation:** Test results appear in the bottom panel — each test shows ✓ or ✗ with expected vs actual values. Score percentage shown.
- **Time:** 2-10 seconds.

## Candidate Completes Assessment
- **Before:** Submit has been used at least once. "Complete & Advance" button is enabled.
- **After clicking Complete & Advance:** Confirmation dialog appears. After clicking OK, shows loading state.
- **Success confirmation:** Redirected to /portal. Status should have advanced.
- **Time:** 2-5 seconds.

## Candidate Status Change (Select/Reject)
- **Before:** Candidate detail page shows current status and Select/Reject buttons.
- **After clicking Select or Reject:** Button shows loading state.
- **Success confirmation:** Status badge updates to new status. Page may refresh.
- **Time:** 1-3 seconds.

## Interviewer Submits Feedback
- **Before:** Feedback form is filled with scores and notes.
- **After clicking Submit Feedback:** Button shows loading state.
- **Success confirmation:** Form may reset or show a success message.
- **Time:** 2-5 seconds.

## Filter Candidates
- **Before:** Full candidate table with all results.
- **After typing a filter value:** Table updates automatically (may have a brief delay).
- **Time:** 1-3 seconds after you stop typing.

## CSV Download
- **Before:** Candidate table has data.
- **After clicking download:** A CSV file downloads to your computer.
- **Success confirmation:** File appears in your downloads folder.
- **Time:** Instant (browser download).

## Login with Wrong Password
- **Before:** Login form filled with wrong password.
- **After clicking Sign In:** Brief loading.
- **Expected:** Red error box appears with error message like "Invalid credentials" or "Login failed".
- **Time:** 1-3 seconds.

## Accessing Restricted Page
- **Before:** You are logged in as a role that should not access a page.
- **After navigating to that page:** You are either redirected to your home page, or see an error/blank page.
- **Expected:** You should NOT see the restricted content. You should be redirected away.

---

# SECTION 6 — KNOWN ISSUES & LIMITATIONS

These are bugs, missing features, or incomplete parts of the application. Test them but do NOT report them as bugs — they are already known. Flag them only if they cause the application to crash or behave unexpectedly in a NEW way.

---

## Issue 1: Email Notifications Not Sending

**Status:** Known (ignore unless crash)

**What is broken:** The system tries to send emails (welcome emails, password reset emails, assessment invitations, status change notifications) but cannot because the email service (SendGrid) has no API key configured.

**Which role/page affected:** All roles. Password reset (Forgot Password), OTP verification, registration confirmation emails.

**What should happen:** Emails should be sent to users.

**What actually happens:** The system returns a success message (e.g., "Check your email") but no email is actually sent. The "Check your email" page shows after Forgot Password but nothing arrives in your inbox.

**Tester action:** Note this as "Known Issue — Email Not Sending". Do not report as a bug. If the application CRASHES or shows an ERROR on these pages (not just silently failing), then report that.

---

## Issue 2: passRatePerRound Shows Fake Numbers

**Status:** Known (ignore)

**What is broken:** The Analytics page shows a "Pass Rate Per Round" bar chart with values 75%, 60%, 45%. These are hardcoded/mock values, not real calculations.

**Which page affected:** /analytics (for HR, Admin, Super Admin)

**What should happen:** The chart should show real pass rates calculated from actual candidate data.

**What actually happens:** The chart always shows Round 1 = 75%, Round 2 = 60%, Round 3 = 45%.

**Tester action:** Note the values are fake. Test that the chart RENDERS properly (bars show, labels visible, no errors).

---

## Issue 3: collegeBreakdown and branchPerformance Show Empty

**Status:** Known (ignore)

**What is broken:** The Analytics page has "College-wise Breakdown" and "Branch-wise Performance" bar charts that are empty.

**Which page affected:** /analytics

**What should happen:** Charts should show real data grouped by college and branch.

**What actually happens:** Empty charts with no bars.

**Tester action:** Test that the charts render WITHOUT errors. Empty charts are expected. If the page CRASHES or shows a JavaScript error, report that.

---

## Issue 4: No HR UI to Assign Assessments to Candidates

**Status:** Known (ignore)

**What is broken:** HR has no interface to select candidates and assign them to assessments (Round 2, Round 3).

**Which page affected:** /dashboard (HR), candidate pipeline

**What should happen:** HR should be able to select candidates and click "Assign Assessment" to start their next round.

**What actually happens:** There is no such button or interface. Candidates can only start assessments from their own portal.

**Tester action:** Do NOT report this as a bug. It is a known missing feature.

---

## Issue 5: No Automatic Status Progression Beyond Round 1

**Status:** Known (ignore)

**What is broken:** The candidate status pipeline should automatically progress through rounds (Applied → Eligible → Round 2 → Round 3 → Interviewed → Selected). Currently, the automatic progression stops after Round 1 (screening).

**Which page affected:** All — candidate status flow

**What should happen:** Completing Round 2 assessment should automatically move candidate to Round 3 status.

**What actually happens:** The status may not change after assessment completion, or may jump directly to "Selected" unexpectedly.

**Tester action:** Observe and document what happens. Do NOT report as new bug if status doesn't progress — this is known. But if the app crashes or shows errors during status changes, report that.

---

## Issue 6: Bulk Actions (Multi-Select) Missing from HR Dashboard

**Status:** Known (ignore)

**What is broken:** HR cannot select multiple candidates at once to perform batch actions (bulk assign, bulk reject, bulk move).

**Which page affected:** /dashboard

**What should happen:** Checkboxes on each row + "Select All" + action buttons in toolbar.

**What actually happens:** No multi-select functionality exists.

**Tester action:** Known missing feature. Do not report.

---

## Issue 7: WebSocket Proctoring Not Implemented

**Status:** Known (ignore)

**What is broken:** The proctoring system (tab switch detection, face monitoring, copy-paste detection) is planned but not yet built.

**Which page affected:** /assessment (candidate)

**What should happen:** During assessments, the system should detect if the candidate switches tabs or copies text, and log the violation.

**What actually happens:** No proctoring happens during assessments.

**Tester action:** Known missing feature. Do not report. If there is a "Proctoring" tab in Candidate Detail that crashes or shows errors, report THAT as a bug.

---

## Issue 8: /docs Page Publicly Accessible (Debug Mode)

**Status:** Known — Configuration Warning

**What is broken:** The backend API documentation page (/docs) is publicly accessible because DEBUG mode is enabled.

**Which page affected:** https://....ngrok-free.dev/docs

**What should happen:** In production, this page should be hidden or require authentication.

**What actually happens:** Anyone can access /docs and see all API endpoints.

**Tester action:** Note this as a configuration warning. Do NOT report as a bug — it's intentional for development. Check that the page loads (it should show Swagger UI).

---

## Issue 9: Analytics Total Candidates Shows Wrong Number

**Status:** Known (ignore)

**What is broken:** The "Total Candidates" stat on the Analytics page shows "1,240" regardless of actual data.

**Which page affected:** /analytics

**Tester action:** Known mock data. Do not report.

---

## Issue 10: Question Generation May Fail (AI API Key)

**Status:** Known (may not work)

**What is broken:** The "Generate Question" button on the Assessment page may fail because the AI API key may not be configured or the AI service may not be accessible.

**Which page affected:** /assessment (candidate), /jobs (HR question generation)

**What should happen:** AI generates a coding problem.

**What actually happens:** May show an error or silently fail.

**Tester action:** Test it. If it fails, note it and continue testing with pre-loaded questions (if available). Report if the failure causes the page to crash or show unhandled errors.

---

## Issue 11: Candidate Status May Auto-Move to SELECTED

**Status:** Known (ignore)

**What is broken:** Sometimes candidates' status changes to "SELECTED" without going through the proper assessment rounds.

**Which page affected:** All candidate-related pages.

**Tester action:** Known bug. Do not report unless it causes a crash.

---

## Issue 12: No Assessment Results View for HR

**Status:** Known (ignore)

**What is broken:** HR cannot see a candidate's code submissions, test results, or detailed assessment performance.

**Which page affected:** /candidates/:id

**What should happen:** The candidate detail page should show assessment submissions, code, and test results.

**What actually happens:** Only scores are shown (if available). No code or test details.

**Tester action:** Known missing feature. Do not report.

---

## Issue 13: Forgot Password Email = TODO Stub

**Status:** Known (ignore)

**What is broken:** The forgot password feature returns success but no email is actually sent (see Issue 1).

**Which page affected:** /forgot-password

**Tester action:** Known. Do not report. Test the UI flow only (form entry, button click, page transition).

---

# SECTION 7 — WHAT TO TEST (Complete Checklist)

Instructions: Go through each item. Tick PASS if it works correctly. Tick FAIL if it doesn't. If in doubt, mark FAIL and take a screenshot.

---

## AUTHENTICATION (All Roles) — Est. 10 minutes

### Landing Page
- [ ] PASS / FAIL: Landing page loads without errors
- [ ] PASS / FAIL: "Login" button goes to /login
- [ ] PASS / FAIL: "Apply Now" goes to /register
- [ ] PASS / FAIL: Theme toggle switches between dark and light mode
- [ ] PASS / FAIL: Features section renders 4 cards with icons

### Login
- [ ] PASS / FAIL: Login page loads at /login
- [ ] PASS / FAIL: Can type email and password
- [ ] PASS / FAIL: "Forgot password?" link goes to /forgot-password
- [ ] PASS / FAIL: "Apply now" link goes to /register
- [ ] PASS / FAIL: Login with correct credentials redirects to correct home page
- [ ] PASS / FAIL: Login with wrong password shows error message (red box)
- [ ] PASS / FAIL: Login with empty fields shows validation error or prevents submission

### Register
- [ ] PASS / FAIL: Register page loads at /register
- [ ] PASS / FAIL: All form fields are visible (name, email, password, college, branch, CGPA, year, language)
- [ ] PASS / FAIL: Resume upload area is visible and clickable
- [ ] PASS / FAIL: Can upload a PDF file as resume
- [ ] PASS / FAIL: "Remove" button clears uploaded resume
- [ ] PASS / FAIL: File larger than 5MB shows error
- [ ] PASS / FAIL: CGPA validation: 0-10 range enforced
- [ ] PASS / FAIL: Year validation: 2000-2030 enforced
- [ ] PASS / FAIL: Registration with new email creates account and redirects
- [ ] PASS / FAIL: Registration with existing email shows error
- [ ] PASS / FAIL: "Sign in" link goes to /login

### Forgot Password
- [ ] PASS / FAIL: Page loads at /forgot-password
- [ ] PASS / FAIL: After entering email and clicking "Send Reset Link", page changes to "Check your email"
- [ ] PASS / FAIL: "Back to sign in" links work

### OTP Verification
- [ ] PASS / FAIL: Page loads at /verify-otp after registration
- [ ] PASS / FAIL: Shows email address (if available)
- [ ] PASS / FAIL: "Resend code" button exists

---

## CANDIDATE PORTAL — Est. 10 minutes

- [ ] PASS / FAIL: /portal loads with profile card showing name, email, college, branch, CGPA
- [ ] PASS / FAIL: Status badge shows correct current status
- [ ] PASS / FAIL: Application Progress pipeline shows 6 steps with current step highlighted
- [ ] PASS / FAIL: "Next Step" section shows contextual guidance text
- [ ] PASS / FAIL: If eligible, "Start Assessment" button appears
- [ ] PASS / FAIL: Active Assessments card appears when assessments exist
- [ ] PASS / FAIL: Past Results card shows scores when available
- [ ] PASS / FAIL: Selected status shows green congratulations message
- [ ] PASS / FAIL: Rejected status shows red not-selected message

---

## CANDIDATE ASSESSMENT — Est. 15 minutes

- [ ] PASS / FAIL: /assessment loads with split-screen layout
- [ ] PASS / FAIL: Round badge shows "2" or "3" correctly
- [ ] PASS / FAIL: Timer is visible and counting down
- [ ] PASS / FAIL: "Generate Question" button works (or gracefully fails)
- [ ] PASS / FAIL: Topic input and difficulty dropdown are functional
- [ ] PASS / FAIL: When question loads, title, description, and test cases are visible
- [ ] PASS / FAIL: Language selector shows Python, Java, C++ options
- [ ] PASS / FAIL: Code editor allows typing code
- [ ] PASS / FAIL: Custom Input textarea accepts text
- [ ] PASS / FAIL: "Run" button executes code and shows output in bottom panel
- [ ] PASS / FAIL: "Submit" button evaluates code and shows test results
- [ ] PASS / FAIL: Submit results show pass/fail per test case with expected vs actual
- [ ] PASS / FAIL: Submit results show score percentage
- [ ] PASS / FAIL: "Complete & Advance" button shows confirmation dialog
- [ ] PASS / FAIL: After completing assessment, redirected to /portal
- [ ] PASS / FAIL: Switching language swaps boilerplate code

---

## HR DASHBOARD — Est. 20 minutes

- [ ] PASS / FAIL: /dashboard loads with all stats cards visible
- [ ] PASS / FAIL: Total Candidates count shows on stats card
- [ ] PASS / FAIL: Applied → Passed card shows screening counts
- [ ] PASS / FAIL: R2 In Progress, R3 In Progress, Interview Scheduled, Selected counts show
- [ ] PASS / FAIL: Average CGPA and Completion Rate show
- [ ] PASS / FAIL: Funnel stage cards show: Eligible, In Assessment, Interviewed, Selected
- [ ] PASS / FAIL: Candidate table loads with data
- [ ] PASS / FAIL: Table shows all columns: Name, College, Branch, Docs, Year, Language, Updated, CGPA, Status
- [ ] PASS / FAIL: Docs column shows icons for resume, govt ID, phone
- [ ] PASS / FAIL: Status badges show correct colors (green for selected, red for rejected, etc.)
- [ ] PASS / FAIL: Sorting works — clicking column headers sorts data
- [ ] PASS / FAIL: Pagination works — page numbers and next/prev navigate
- [ ] PASS / FAIL: "Run Screening" button works and shows results
- [ ] PASS / FAIL: CSV Download button downloads a .csv file
- [ ] PASS / FAIL: Search box filters candidates by name

### HR Filters
- [ ] PASS / FAIL: "Pipeline Filters" toggle expands/collapses filter panel
- [ ] PASS / FAIL: Branch filter text input filters table
- [ ] PASS / FAIL: College filter text input filters table
- [ ] PASS / FAIL: Status dropdown filters by status
- [ ] PASS / FAIL: CGPA Min/Max fields filter by CGPA range
- [ ] PASS / FAIL: Date filters (Created After/Before) filter by date
- [ ] PASS / FAIL: "Reset All Filters" clears all filters

---

## HR CANDIDATE DETAIL — Est. 5 minutes

- [ ] PASS / FAIL: Clicking candidate name goes to /candidates/:id
- [ ] PASS / FAIL: Profile card shows name, email, college, branch, CGPA, status
- [ ] PASS / FAIL: Avatar shows first letter of name
- [ ] PASS / FAIL: "Select" button changes status to Selected
- [ ] PASS / FAIL: "Reject" button changes status to Rejected
- [ ] PASS / FAIL: Scores tab shows assessment scores or "No scores yet."
- [ ] PASS / FAIL: "Back" button navigates to previous page

---

## INTERVIEW PANEL — Est. 10 minutes

- [ ] PASS / FAIL: /interview loads with left panel (candidate list) and right panel (details)
- [ ] PASS / FAIL: Candidate list shows names and colleges
- [ ] PASS / FAIL: Clicking a candidate shows their info on the right
- [ ] PASS / FAIL: Assessment scores display on right panel
- [ ] PASS / FAIL: Technical Score slider works (0-10, number updates)
- [ ] PASS / FAIL: Communication Score slider works (0-10, number updates)
- [ ] PASS / FAIL: Recommendation buttons toggle: Select / Hold / Reject
- [ ] PASS / FAIL: Notes textarea accepts text
- [ ] PASS / FAIL: "Submit Feedback" button works
- [ ] PASS / FAIL: Empty state shows "No candidates assigned" when list is empty
- [ ] PASS / FAIL: No-candidate-selected state shows "Select a candidate to provide feedback"

---

## SELECTION PANEL — Est. 5 minutes

- [ ] PASS / FAIL: /selection loads with "Final Selection" title
- [ ] PASS / FAIL: Shows count of candidates ready for decision
- [ ] PASS / FAIL: Candidate cards show name, college, branch, CGPA, scores
- [ ] PASS / FAIL: Toggle switches work (on = select, off = reject)
- [ ] PASS / FAIL: "Confirm All Decisions" button works
- [ ] PASS / FAIL: Empty state shows "No candidates ready for selection" when no candidates
- [ ] PASS / FAIL: Footer shows "Select" or "Reject" based on toggle position

---

## ANALYTICS DASHBOARD — Est. 5 minutes

- [ ] PASS / FAIL: /analytics loads without errors
- [ ] PASS / FAIL: Total Candidates card displays
- [ ] PASS / FAIL: Pass Rate Per Round bar chart renders (3 bars, values 75/60/45)
- [ ] PASS / FAIL: Hiring Funnel chart renders with stage counts
- [ ] PASS / FAIL: College-wise Breakdown bar chart renders (even if empty)
- [ ] PASS / FAIL: Branch-wise Performance bar chart renders (even if empty)
- [ ] PASS / FAIL: Proctoring Violations section renders (even if empty)
- [ ] PASS / FAIL: No JavaScript "Cannot read properties of undefined" errors

---

## SUPER ADMIN PANEL — Est. 5 minutes

- [ ] PASS / FAIL: /superadmin loads with 3 stat cards
- [ ] PASS / FAIL: Users & Roles table shows all users with names, emails, roles, statuses, dates
- [ ] PASS / FAIL: Role badges show correct colors
- [ ] PASS / FAIL: Status badges show correct colors
- [ ] PASS / FAIL: Tab switching between "Users & Roles" and "Pipeline Summary" works
- [ ] PASS / FAIL: Pipeline Summary tab shows descriptive message

---

## ADMIN DASHBOARD — Est. 5 minutes

- [ ] PASS / FAIL: /admin loads with "Admin Dashboard" title
- [ ] PASS / FAIL: "Audit Logs" tab loads log entries (or shows empty message)
- [ ] PASS / FAIL: "Export DB" tab shows description and download button
- [ ] PASS / FAIL: "Download DB Export" downloads a JSON file
- [ ] PASS / FAIL: Downloaded JSON file has content (not empty)

---

## JOB MANAGEMENT — Est. 5 minutes

- [ ] PASS / FAIL: /jobs loads with stats cards
- [ ] PASS / FAIL: Job table loads (or shows empty state)
- [ ] PASS / FAIL: "New Job" button shows create form
- [ ] PASS / FAIL: Create Job form accepts title and description
- [ ] PASS / FAIL: Creating a job adds it to the table
- [ ] PASS / FAIL: "Close" and "Reopen" buttons toggle job status
- [ ] PASS / FAIL: "Generate Questions" button opens modal
- [ ] PASS / FAIL: Question generation modal has topic input and difficulty dropdown

---

## SETTINGS — Est. 3 minutes

- [ ] PASS / FAIL: /settings shows account info (name, email, role)
- [ ] PASS / FAIL: "Delete Account" button expands danger zone
- [ ] PASS / FAIL: Password input and confirm/cancel buttons appear on delete click
- [ ] PASS / FAIL: "Cancel" hides the delete confirmation

---

## NAVIGATION & SIDEBAR — Est. 5 minutes

- [ ] PASS / FAIL: Sidebar shows correct links based on role
- [ ] PASS / FAIL: HR sees: Dashboard, Jobs, Candidates, Selection, Analytics, Settings
- [ ] PASS / FAIL: Interviewer sees: Candidates, Interview Panel (in sidebar)
- [ ] PASS / FAIL: Admin sees: Dashboard, Jobs, Candidates, Selection, Analytics, Interview, Settings + /admin
- [ ] PASS / FAIL: Super Admin sees: All of the above + Super Admin link
- [ ] PASS / FAIL: Candidate sees: Portal, Assessment (candidate-specific nav)
- [ ] PASS / FAIL: Clicking sidebar links navigates correctly

---

## ERROR & EDGE CASES — Est. 10 minutes

- [ ] PASS / FAIL: Navigating to invalid URL shows redirect (not a blank white page)
- [ ] PASS / FAIL: Trying to access /superadmin as HR redirects away
- [ ] PASS / FAIL: Trying to access /interview as HR redirects away
- [ ] PASS / FAIL: Trying to access /portal as HR redirects away
- [ ] PASS / FAIL: Trying to access /dashboard as Candidate redirects away
- [ ] PASS / FAIL: Registering with special characters in name (e.g., "O'Brien")
- [ ] PASS / FAIL: Very long name (50+ characters) handles gracefully
- [ ] PASS / FAIL: CGPA = 0.00 or 10.00 handles correctly
- [ ] PASS / FAIL: Empty candidate table shows appropriate message
- [ ] PASS / FAIL: Logging out clears session and returns to login page

---

# SECTION 8 — WHAT TO SCREENSHOT

## Screenshot EVERY page after login (one per role per page)

For each role, log in and screenshot every page they can access:

**Candidate:**
1. candidate_portal_page.png
2. candidate_assessment_page.png

**HR:**
3. hr_dashboard_page.png
4. hr_dashboard_filters_expanded.png
5. hr_candidate_detail_page.png
6. hr_selection_page.png
7. hr_analytics_page.png
8. hr_jobs_page.png
9. hr_settings_page.png

**Interviewer:**
10. interviewer_panel_page.png
11. interviewer_panel_with_candidate_selected.png

**Admin:**
12. admin_dashboard_page.png
13. admin_audit_logs.png
14. admin_export_tab.png

**Super Admin:**
15. superadmin_panel_users.png
16. superadmin_panel_pipeline.png

## Screenshot EVERY error message

- Any red error box on login/register
- Any "Failed to load" message
- Any 500-type page error
- Any "Cannot read properties of undefined" (check browser console for this)

## Screenshot EVERY broken UI element

- Misaligned text or buttons
- Overlapping elements
- Missing images or icons (showing broken image icon)
- Text that is cut off or overflowed
- Buttons that don't respond to clicks

## Screenshot EVERY success confirmation

- After running screening → screenshot the "Screened: X passed" message
- After submitting interview feedback → screenshot the result
- After completing assessment → screenshot the redirect page
- After CSV download → screenshot the download prompt or the CSV contents

## Before and After major actions

- Candidate list before and after running screening
- Candidate status before and after clicking Select/Reject
- Filter panel before and after applying filters

## Naming Convention

Save ALL screenshots in: **/testing/YYYY-MM-DD/** (create folders as needed)

File name format: **{role}_{page}_{action}_{pass_or_fail}.png**

Examples:
- `hr_dashboard_load_pass.png`
- `hr_dashboard_filters_not_working_fail.png`
- `candidate_assessment_timer_shows_pass.png`
- `interviewer_submit_feedback_success_pass.png`
- `admin_export_download_fail.png`
- `superadmin_users_table_pass.png`

---

# SECTION 9 — TEST CREDENTIALS

## All Test Accounts

| Role | Email | Password | Home Page |
|------|-------|----------|-----------|
| **Super Admin** | admin@knowledgefactory.com | Admin123! | /superadmin |
| **HR Manager** | hr@knowledgefactory.com | HR123! | /dashboard |
| **Interviewer** | interviewer@knowledgefactory.com | Interview123! | /interview |
| **Candidate 1** | candidate1@student.edu | Candidate123! | /portal |
| **Candidate 2** | candidate2@student.edu | Candidate123! | /portal |

## How to Verify Accounts Work

1. Open Chrome in Incognito Mode (or clear cookies/localStorage between role switches).
2. Go to the live URL.
3. Click "Sign In".
4. Enter the email and password for the role you want to test.
5. If login is successful, you'll be redirected to the role's home page.
6. If login fails, you'll see a red error box. Note the error and take a screenshot.

## Creating Additional Test Candidates

You can register new candidates directly from the website:
1. From the landing page, click "Apply Now".
2. Fill in the form with test data.
3. Use a unique email each time (e.g., qatest_1@test.com, qatest_2@test.com).
4. Use "TestPass123!" as password for all test accounts.

---

# SECTION 10 — HOW TO REPORT ISSUES

## Bug Report Template

For every bug you find, document it in the following format. Copy this template and fill it in.

```
---
## BUG REPORT #{number}

**Page URL:** (e.g., https://....ngrok-free.dev/dashboard)
**Role Logged In As:** (e.g., HR Manager)
**Date Found:** YYYY-MM-DD

**Steps to Reproduce:**
1. Log in as [role]
2. Navigate to [page]
3. Click on [button/link]
4. ...

**Expected Result:**
(What should happen according to this document)

**Actual Result:**
(What actually happened)

**Screenshot(s):**
(Filename(s) of screenshots)

**Browser Console Errors (if any):**
(Paste any red errors from Chrome DevTools Console — press F12 → Console tab)

**Severity:**
[Blocker / Major / Minor / Cosmetic]
```

## Severity Guide

| Severity | Meaning | Example |
|----------|---------|---------|
| **Blocker** | Cannot proceed with testing at all | Login page won't load, entire page is blank |
| **Major** | Feature doesn't work as intended | "Select" button does nothing, form won't submit, filter doesn't work |
| **Minor** | Feature works but something is wrong or looks odd | Wrong count shown, text is misspelled, button is slightly misaligned |
| **Cosmetic** | Small visual issue, doesn't affect function | Color slightly off, padding uneven, font size inconsistent |

## When to Flag vs. Report

**Flag as KNOWN ISSUE (do not report as bug):**
- Any issue listed in Section 6
- Email not sending
- Mock data in analytics
- Empty charts
- Missing features (bulk upload, assessment assignment, etc.)

**REPORT as a bug:**
- Page crash or blank white screen (Blocker)
- Button that does nothing when clicked (Major)
- Form submission that shows no response (Major)
- Navigation that goes to wrong page (Major)
- Data that disappears after refresh (Major)
- Typo, alignment issue, color problem (Minor/Cosmetic)
- ANY error message in the browser's developer console when performing an action (open F12 → Console tab)

## What to Do If Something Is Unclear

1. Re-read the relevant section of this document.
2. Try the action again, step by step.
3. Check if you are logged in as the correct role.
4. Check the URL — are you on the right page?
5. Take a screenshot of what you see.
6. Document it in your report with the screenshot.
7. Move on to the next test item.

---

## END OF DOCUMENT

**Total testing time estimate: 6-8 hours**

Thank you for testing Knowledge Factory. Your thorough testing helps make this platform reliable and user-friendly for real hiring teams and candidates.
