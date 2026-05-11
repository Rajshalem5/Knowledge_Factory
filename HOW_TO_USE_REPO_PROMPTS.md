# How to Use Repository Analysis Prompts

## Overview

I've created **2 prompts** for AI assistants that can read your entire codebase:

1. **`PROMPT_FOR_AI_WITH_REPO_ACCESS.md`** - Comprehensive (detailed analysis + implementation)
2. **`QUICK_PROMPT_WITH_REPO.md`** - Quick version (faster analysis)

---

## Which AI Assistants Can Use These?

### ✅ AI with Codebase Access
- **Cursor AI** (recommended)
- **GitHub Copilot Chat** (with workspace context)
- **Claude** (with file upload/project context)
- **Windsurf**
- **Cody by Sourcegraph**
- **Aider**
- **Continue.dev**

### ❌ AI WITHOUT Codebase Access
- ChatGPT (web version) - Use `AI_PROMPT_FOR_MISSING_FEATURES.md` instead
- Claude (web version without files) - Use `AI_PROMPT_FOR_MISSING_FEATURES.md` instead
- Gemini - Use `AI_PROMPT_FOR_MISSING_FEATURES.md` instead

---

## How to Use with Cursor AI (Recommended)

### Step 1: Open Your Project in Cursor
```bash
cd /path/to/Knowledge_Factory
cursor .
```

### Step 2: Open Cursor Chat
- Press `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux)
- Or click the chat icon in the sidebar

### Step 3: Enable Codebase Context
- In the chat input, type `@Codebase` to include entire codebase
- Or click the "+" button and select "Codebase"

### Step 4: Paste the Prompt
Copy the entire content of either:
- `PROMPT_FOR_AI_WITH_REPO_ACCESS.md` (comprehensive)
- `QUICK_PROMPT_WITH_REPO.md` (quick)

Paste into Cursor chat.

### Step 5: Add PRD Reference
Before sending, add:
```
Also read the PRD document at: Knowledge Factory -Talent Hiring Portal (Product UseCase Document) (1).pdf
```

### Step 6: Send and Wait
Cursor will:
1. Read the PRD
2. Analyze your entire codebase
3. Compare PRD vs implementation
4. List all issues
5. Provide implementation plan

---

## How to Use with GitHub Copilot Chat

### Step 1: Open in VS Code
```bash
cd /path/to/Knowledge_Factory
code .
```

### Step 2: Open Copilot Chat
- Press `Cmd+Shift+I` (Mac) or `Ctrl+Shift+I` (Windows/Linux)
- Or click the Copilot icon in the sidebar

### Step 3: Use Workspace Context
Type in chat:
```
@workspace
```

### Step 4: Paste the Prompt
Copy and paste either:
- `PROMPT_FOR_AI_WITH_REPO_ACCESS.md`
- `QUICK_PROMPT_WITH_REPO.md`

### Step 5: Reference PRD
Add:
```
Read the PRD: Knowledge Factory -Talent Hiring Portal (Product UseCase Document) (1).pdf
```

### Step 6: Send
Copilot will analyze your workspace and provide insights.

---

## How to Use with Claude (Desktop/Projects)

### Step 1: Create a Claude Project
1. Go to Claude.ai
2. Click "Projects" in sidebar
3. Create new project: "Knowledge Factory"

### Step 2: Add Project Files
1. Click "Add content"
2. Upload your entire project folder
3. Or add specific files:
   - PRD document
   - All backend files
   - All frontend files
   - `FUNCTIONALITY_ISSUES.md`

### Step 3: Start Chat
In the project chat, paste:
- `PROMPT_FOR_AI_WITH_REPO_ACCESS.md` (full)
- `QUICK_PROMPT_WITH_REPO.md` (quick)

### Step 4: Claude Analyzes
Claude will read all project files and analyze against PRD.

---

## How to Use with Aider

### Step 1: Install Aider
```bash
pip install aider-chat
```

### Step 2: Navigate to Project
```bash
cd /path/to/Knowledge_Factory
```

### Step 3: Start Aider with Files
```bash
aider --model gpt-4 \
  backend/app/**/*.py \
  app/src/**/*.tsx \
  app/src/**/*.ts
```

### Step 4: Paste Prompt
In Aider chat, paste:
```
Read the PRD at: Knowledge Factory -Talent Hiring Portal (Product UseCase Document) (1).pdf

[Paste PROMPT_FOR_AI_WITH_REPO_ACCESS.md or QUICK_PROMPT_WITH_REPO.md here]
```

### Step 5: Aider Implements
Aider will analyze and make changes directly to your files.

---

## What to Expect

### Phase 1: Analysis (5-10 minutes)
The AI will:
- Read PRD document
- Explore all backend files
- Explore all frontend files
- Check database migrations
- Compare PRD vs implementation

### Phase 2: Report (Output)
You'll get:
```markdown
# Analysis Report

## Summary
- Total PRD features: 45
- Implemented: 15 ✅
- Missing: 20 ❌
- Broken: 10 🐛

## Critical Issues (🔴)
1. Assessment assignment not working
   - Root cause: ...
   - Impact: ...
   - Solution: ...
   - Files: ...

2. Interview scheduling missing
   ...

## High Priority Issues (🟡)
...

## Implementation Plan
Phase 1: Fix critical issues (2-3 days)
Phase 2: Implement missing features (1-2 weeks)
Phase 3: Polish & test (3-5 days)
```

### Phase 3: Implementation
The AI will:
- Create missing files
- Fix broken files
- Add database migrations
- Implement missing features
- Add tests

---

## Tips for Best Results

### 1. Be Patient
Repository analysis takes time. Let the AI read everything.

### 2. Ask Follow-up Questions
After the initial analysis:
```
"Show me the code for fixing issue #1"
"Implement the assessment assignment feature"
"Create the missing database migrations"
```

### 3. Review Changes
Always review AI-generated code before committing.

### 4. Test Incrementally
Test each fix before moving to the next.

### 5. Ask for Clarifications
If something is unclear:
```
"Explain why the assessment workflow is broken"
"What's the correct status transition flow?"
"How should the interview scheduling work?"
```

---

## Comparison: Which Prompt to Use?

### Use `PROMPT_FOR_AI_WITH_REPO_ACCESS.md` when:
- ✅ You want a thorough analysis
- ✅ You want detailed implementation plans
- ✅ You want code examples for every fix
- ✅ You have time for comprehensive review
- ✅ You want to understand every issue deeply

**Time**: 30-60 minutes for analysis + implementation

### Use `QUICK_PROMPT_WITH_REPO.md` when:
- ✅ You want a faster analysis
- ✅ You want to get started quickly
- ✅ You trust the AI to find issues
- ✅ You want a high-level overview first

**Time**: 10-20 minutes for analysis + implementation

---

## Example Workflow

### Day 1: Analysis
1. Open project in Cursor AI
2. Paste `PROMPT_FOR_AI_WITH_REPO_ACCESS.md`
3. Wait for analysis report
4. Review all identified issues
5. Prioritize fixes

### Day 2-3: Critical Fixes
1. Ask AI to implement critical fixes
2. Review and test each fix
3. Commit working fixes

### Day 4-7: High Priority Features
1. Ask AI to implement missing features
2. Test each feature
3. Commit working features

### Day 8-10: Medium Priority
1. Implement remaining features
2. Add proctoring
3. Enhance analytics

### Day 11-12: Testing & Polish
1. End-to-end testing
2. Fix bugs
3. Polish UI
4. Documentation

---

## Troubleshooting

### Issue: AI can't read PRD
**Solution**: 
- Upload PRD separately
- Or extract text from PDF and paste it
- Or describe PRD requirements manually

### Issue: AI analysis is incomplete
**Solution**:
- Use the comprehensive prompt
- Ask AI to "continue analysis"
- Point AI to specific files: "Check backend/app/features/assessments/"

### Issue: AI suggests wrong fixes
**Solution**:
- Review the fix carefully
- Ask AI to explain the reasoning
- Provide more context about expected behavior
- Reference the PRD requirements

### Issue: Too many issues found
**Solution**:
- Focus on critical issues first
- Ask AI to prioritize
- Implement incrementally

---

## Success Criteria

You'll know the analysis is complete when:

✅ All PRD features are listed
✅ Each feature is marked as implemented/missing/broken
✅ All issues have root causes identified
✅ All issues have solutions provided
✅ Implementation plan is clear
✅ File paths are specified
✅ Code examples are provided

---

## Next Steps After Analysis

1. **Review the report** - Understand all issues
2. **Prioritize** - Decide what to fix first
3. **Implement** - Ask AI to implement fixes
4. **Test** - Verify each fix works
5. **Commit** - Save working changes
6. **Repeat** - Move to next priority

---

## Files Created

```
✅ PROMPT_FOR_AI_WITH_REPO_ACCESS.md  (Comprehensive - 500+ lines)
✅ QUICK_PROMPT_WITH_REPO.md          (Quick - 150+ lines)
✅ HOW_TO_USE_REPO_PROMPTS.md         (This file - Instructions)
```

---

## Summary

**For Cursor AI / Copilot / Claude with files**:
1. Open project in AI tool
2. Paste `PROMPT_FOR_AI_WITH_REPO_ACCESS.md` or `QUICK_PROMPT_WITH_REPO.md`
3. Reference PRD document
4. Wait for analysis
5. Review and implement fixes

**For ChatGPT / Claude web (no files)**:
1. Use `AI_PROMPT_FOR_MISSING_FEATURES.md` instead
2. Manually provide context
3. Implement based on detailed instructions

---

**You're all set!** 🚀

Choose your AI tool, paste the appropriate prompt, and let it analyze your entire codebase against the PRD!
