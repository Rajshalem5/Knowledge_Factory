# Production Checklist

Check these before going live.

## Required before launch

- [ ] **Separate file serving domain**: Configure a subdomain (e.g. `files.knowledgefactory.com`) for uploaded files. Same-origin file serving lets malicious uploads access app cookies/localStorage — this is the single highest-impact security defense.
- [ ] Set `DEBUG=false` in production (disables `/docs`, `/redoc`, relaxed CSP, relaxed rate limits)
- [ ] Migrate from SQLite to PostgreSQL
- [ ] Replace in-memory rate limiter with Redis-based (`slowapi` + `redis`)
- [ ] Run `npm audit` and `pip audit` — fix any critical/high vulnerabilities
- [ ] Verify HSTS + CSP headers are present (currently only set in non-DEBUG mode)
- [ ] Add `safety` or `pip audit` to CI pipeline

## Nice to have

- [ ] Global exception handler for consistent error formatting
- [ ] Pin all dependencies to exact versions (replace `>=` with `==`)
- [ ] ClamAV scanning on file uploads
- [ ] Audit logging for all auth failures
