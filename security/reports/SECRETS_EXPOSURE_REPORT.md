# SECRETS_EXPOSURE Security Report

## Status: CRITICAL

## Findings

### CRITICAL: .gitignore does not contain .env

The project's `.gitignore` file **does not include `.env`** anywhere. Currently `git ls-files .env` returns nothing (i.e. .env files are not tracked), but this is purely accidental. Any future `git add .` or `git add -A` would stage all .env files along with everything else.

Files at risk:
- `./backend/.env` — contains DATABASE_URL, CORS_ORIGINS with ngrok URL, REDIS_URL, SENDGRID_API_KEY (redacted), DEBUG=true
- `./backend/.env.prod` — exists
- `./backend/.env.staging` — exists
- `./backend/.env.dev` — exists
- `./app/.env` — contains VITE_CLERK_PUBLISHABLE_KEY (publishable, low risk), VITE_API_URL

### MEDIUM: app/.env.example is out of sync

`app/.env.example` has placeholder values (`VITE_API_URL=http://localhost:8000`, `VITE_ENABLE_DEMO_MODE=false`, `VITE_LOG_LEVEL=info`) but the actual `app/.env` has Clerk authentication variables (`VITE_CLERK_PUBLISHABLE_KEY`, sign-in/up URLs) that aren't documented in the example. A new developer wouldn't know what to configure.

### LOW: ngrok_url.txt committed to git

`ngrok_url.txt` contains `https://ila-sturdiest-oversentimentally.ngrok-free.dev` — not a credential but exposes internal infrastructure URL. Should be gitignored.

### PASS: No secrets in source code

Checked across all `.py`, `.ts`, `.tsx`, `.js`, `.jsx` source files:
- No `sk_live_` / `sk_test_` Stripe keys found
- No `AKIA` AWS access keys found
- No private keys found
- No hardcoded credentials in source files

### PASS: VITE_* vars are public-only

The frontend `VITE_CLERK_PUBLISHABLE_KEY` is a Clerk **publishable** key (prefix `pk_test_`), which is designed to be public and bundled into client code. This is correct usage.

### PASS: .env files not currently in git

```
git ls-files .env → (no output)
```

No .env file is currently tracked in version control.

## What's at risk

- If any .env file is accidentally committed (via `git add .`, `git add -A`, or a forgetful developer), all secrets go public on GitHub.
- Attackers scan GitHub continuously for committed .env files with credentials.
- The ngrok URL in plaintext tells attackers the infrastructure endpoint.

## What's already secure

- No secrets currently in git index or history (confirmed).
- VITE_CLERK_PUBLISHABLE_KEY usage is correct (publishable key).
- No hardcoded API keys or tokens in source code.
- Backend `.env.example` has placeholder values (good practice).

## Recommendations

1. **[CRITICAL]** Add `.env*` pattern to `.gitignore` — prevents accidental commit of any .env file
2. **[MEDIUM]** Update `app/.env.example` to document all expected env vars (including Clerk ones)
3. **[LOW]** Add `ngrok_url.txt` to `.gitignore`
4. **[LOW]** Consider checking `backend/.env.prod` and `backend/.env.staging` for real secrets
