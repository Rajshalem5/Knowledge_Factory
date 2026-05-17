# SECRETS_EXPOSURE Fix Plan

## Changes

- `.gitignore` — add `.env*` pattern to prevent accidental commits
- `app/.env.example` — add Clerk VITE_ variables as documented placeholders
- `ngrok_url.txt` — keep (no change) but add to `.gitignore`

## New files

None

## Verification goals

After implementation, ALL of these must be true:

- [ ] `git ls-files .env` returns nothing
- [ ] `.env*` is listed in `.gitignore`
- [ ] `grep -rn "sk_live_|sk_test_|AKIA" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" app/src/ backend/app/` returns nothing
- [ ] No `VITE_*` env var in source code holds a secret key
- [ ] `app/.env.example` documents all variables from `app/.env` with placeholder values

## Manual verification (for the human)

- Verify `git status` shows no tracked .env files
- Check `backend/.env.prod` and `backend/.env.staging` don't contain real secrets that could leak
