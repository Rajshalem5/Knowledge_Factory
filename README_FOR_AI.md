# Instructions for Using AI Prompts

## Overview

This project has **3 documentation files** to help you get all missing features implemented:

1. **`FUNCTIONALITY_ISSUES.md`** - Complete analysis of all issues
2. **`AI_PROMPT_FOR_MISSING_FEATURES.md`** - Comprehensive prompt for full implementation
3. **`QUICK_START_PROMPT.md`** - Focused prompt for critical features only

---

## Which Prompt to Use?

### Option 1: Full Implementation (Recommended)
**Use**: `AI_PROMPT_FOR_MISSING_FEATURES.md`

**What you get**:
- Complete assessment workflow (Round 2 & 3)
- Interview management system
- Proctoring functionality
- Selection panel
- Enhanced analytics
- All bulk actions
- Status transition validation

**Time estimate**: 20-40 hours of development

**Copy this prompt to AI and say**:
```
Implement all features described in this prompt for my Knowledge Factory 
Talent Hiring Portal. Start with Phase 1 (Assessment Workflow) and work 
through all phases sequentially.
```

---

### Option 2: Critical Features Only (Quick Start)
**Use**: `QUICK_START_PROMPT.md`

**What you get**:
- Assessment assignment by HR
- Candidate assessment portal
- Assessment results view
- Status transition validation
- Basic bulk actions

**Time estimate**: 8-12 hours of development

**Copy this prompt to AI and say**:
```
Implement the critical assessment workflow features described in this 
prompt. Focus on getting candidates from ROUND1_PASSED through Round 2 
and Round 3 assessments to SELECTED status.
```

---

### Option 3: Just Read the Issues
**Use**: `FUNCTIONALITY_ISSUES.md`

**What you get**:
- Understanding of all problems
- List of missing features
- Priority recommendations
- No implementation guidance

**Use this when**:
- You want to understand what's broken
- You want to plan your own implementation
- You want to assign tasks to your team

---

## How to Use These Prompts

### Step 1: Choose Your Approach
- **Full implementation**: Use `AI_PROMPT_FOR_MISSING_FEATURES.md`
- **Quick start**: Use `QUICK_START_PROMPT.md`

### Step 2: Copy the Entire Prompt
Open the chosen file and copy **everything** from start to finish.

### Step 3: Paste to AI Assistant
Paste into:
- ChatGPT (GPT-4 or Claude)
- Claude (Sonnet 3.5 or Opus)
- Cursor AI
- GitHub Copilot Chat
- Any other AI coding assistant

### Step 4: Add Context (Optional)
If the AI needs more context, also provide:
- Your project structure
- Current working features
- Specific requirements or constraints

### Step 5: Follow Implementation Order
The prompts include implementation order. Follow it sequentially:
1. Backend endpoints first
2. Then frontend UI
3. Then integration testing

---

## What's Already Fixed

✅ **All backend routes are now enabled**:
- `/api/assessment/*` - Assessment management
- `/api/code/*` - Code execution
- `/api/questions/*` - Question bank
- `/api/proctoring/*` - Proctoring events
- `/api/interviews/*` - Interview scheduling
- `/api/selection/*` - Final selection

These were commented out before. They're now active and ready to use.

---

## What Still Needs Implementation

### High Priority (Do First)
1. ❌ Assessment assignment interface (HR)
2. ❌ Assessment taking interface (Candidate)
3. ❌ Assessment results view (HR)
4. ❌ Status transition validation
5. ❌ Bulk actions for candidates

### Medium Priority (Do Second)
6. ❌ Interview scheduling interface
7. ❌ Interview feedback form
8. ❌ Proctoring dashboard
9. ❌ Selection panel

### Low Priority (Do Last)
10. ❌ Enhanced analytics with real data
11. ❌ Notifications system
12. ❌ Complete bulk upload

---

## Example: Using the Full Prompt

### Copy this to your AI:

```
I have a Knowledge Factory Talent Hiring Portal with React frontend and 
FastAPI backend. I need to implement all missing features described in 
the attached prompt.

Current status:
- Authentication works
- Candidate listing works
- Screening works (APPLIED → ROUND1_PASSED)
- Basic analytics works

Missing:
- Assessment workflow (Round 2 & 3)
- Interview management
- Proctoring
- Selection process

Please implement all features in the order specified in the prompt, 
starting with Phase 1: Assessment Assignment & Management.

[PASTE ENTIRE CONTENT OF AI_PROMPT_FOR_MISSING_FEATURES.md HERE]
```

---

## Example: Using the Quick Start Prompt

### Copy this to your AI:

```
I need to implement the critical assessment workflow for my Knowledge 
Factory Talent Hiring Portal. Currently, candidates get stuck at 
ROUND1_PASSED status and cannot progress through Round 2 and Round 3 
assessments.

Please implement the 6 tasks described in this prompt to enable the 
complete assessment workflow.

[PASTE ENTIRE CONTENT OF QUICK_START_PROMPT.md HERE]
```

---

## Tips for Best Results

### 1. Be Specific About Your Stack
Tell the AI:
- "I'm using React 18 with TypeScript"
- "Backend is FastAPI with Python 3.12"
- "Database is PostgreSQL"
- "Using Monaco Editor for code editor"

### 2. Ask for Incremental Implementation
Instead of "implement everything", say:
- "Start with Task 1.2: Backend assessment assignment endpoint"
- "Show me the complete code for this endpoint"
- "Now implement Task 1.1: HR assessment assignment UI"

### 3. Request Testing Instructions
After each feature, ask:
- "How do I test this feature?"
- "What API calls should I make to verify it works?"
- "What should I see in the UI?"

### 4. Ask for Clarifications
If something is unclear:
- "What should the assessment assignment modal look like?"
- "How should I handle assessment deadline validation?"
- "Should assessments have time limits?"

### 5. Request Code Reviews
After implementation:
- "Review this code for security issues"
- "Check if status transitions are properly validated"
- "Verify error handling is complete"

---

## Common Questions

### Q: Do I need to implement everything?
**A**: No. Start with the Quick Start prompt to get the critical assessment workflow working. Then add other features as needed.

### Q: Can I modify the implementation?
**A**: Yes! The prompts are guidelines. Adapt them to your specific needs.

### Q: What if the AI makes mistakes?
**A**: Review the code, test thoroughly, and ask the AI to fix issues. Reference the `FUNCTIONALITY_ISSUES.md` for expected behavior.

### Q: Should I implement in one go or incrementally?
**A**: Incrementally! Implement one task, test it, then move to the next.

### Q: What if I get stuck?
**A**: Refer back to `FUNCTIONALITY_ISSUES.md` for the big picture, or ask the AI to explain a specific part.

---

## File Structure Reference

```
.
├── FUNCTIONALITY_ISSUES.md           # Complete analysis
├── AI_PROMPT_FOR_MISSING_FEATURES.md # Full implementation prompt
├── QUICK_START_PROMPT.md             # Critical features prompt
├── README_FOR_AI.md                  # This file
├── app/                              # Frontend
│   └── src/
│       ├── pages/hr/                 # HR interfaces
│       ├── pages/candidate/          # Candidate portal
│       └── components/               # Reusable components
└── backend/                          # Backend
    └── app/
        ├── features/                 # Feature modules
        │   ├── assessments/          # Assessment routes
        │   ├── interviews/           # Interview routes
        │   └── candidates/           # Candidate routes
        └── main.py                   # FastAPI app (routes enabled)
```

---

## Success Criteria

You'll know the implementation is complete when:

✅ HR can assign Round 2 assessments to eligible candidates
✅ Candidates can see and take assigned assessments
✅ Candidates can write code and execute tests
✅ Candidates can submit assessments
✅ HR can view assessment results and scores
✅ HR can pass/reject candidates based on results
✅ Candidate status updates automatically through the workflow
✅ HR can assign Round 3 assessments to Round 2 passed candidates
✅ HR can schedule interviews for Round 3 passed candidates
✅ Interviewers can submit feedback
✅ HR can select/reject candidates after interviews
✅ All status transitions are validated
✅ Bulk actions work for multiple candidates

---

## Need Help?

If you're stuck or need clarification:
1. Read `FUNCTIONALITY_ISSUES.md` for context
2. Check the "Questions to Ask" section in the full prompt
3. Ask the AI to explain a specific part
4. Break down the task into smaller steps

---

## Good Luck! 🚀

Start with the Quick Start prompt if you want to see results fast, or use the full prompt if you want a complete implementation.

Remember: Implement incrementally, test frequently, and don't hesitate to ask the AI for clarifications!
