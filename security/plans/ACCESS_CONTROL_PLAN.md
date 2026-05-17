# ACCESS_CONTROL Fix Plan

## Changes

- `backend/app/features/assessments/routes.py` — Add `candidate_id` ownership check to `GET /{assessment_id}` (FIXED)

## Verification goals

- [ ] `GET /api/assessment/{assessment_id}` with another candidate's assessment ID returns 404
- [ ] `GET /api/assessment/{assessment_id}` with own assessment ID still works
