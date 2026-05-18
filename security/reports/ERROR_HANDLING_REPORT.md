# ERROR_HANDLING Security Report

## Status: LOW → FIXED

## Findings

### FIXED: No global exception handler

**Fix applied:**
- Added `SENTRY_DSN` field to `Settings` in `backend/app/core/config.py`
- Wired up Sentry init in `main.py` (was already stubbed but missing config)
- Added catch-all middleware that logs every unhandled 500 and returns clean JSON
- In production: Sentry captures + groups + traces every error
- In development: errors are at least logged server-side with full traceback

### PASS: docs disabled in production
```python
docs_url="/docs" if settings.DEBUG else None,
redoc_url="/redoc" if settings.DEBUG else None,
```

## Recommendations

1. **[LOW]** Add a global exception handler for consistent error formatting and logging of all unhandled errors
2. **[LOW]** Ensure `DEBUG=false` in production (currently depends on env config)
