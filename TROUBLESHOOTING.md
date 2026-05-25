# Troubleshooting Guide

## Common Issues & Resolutions

### 1. Port Already In Use
**Error:** `[Errno 98] Address already in use` or `Error: listen EADDRINUSE: address already in use :::5173`
**Resolution:** 
Find and kill the process using the port.
*   Windows: `netstat -ano | findstr :8000`, then `taskkill /PID <PID> /F`
*   Linux/Mac: `lsof -i :8000`, then `kill -9 <PID>`

### 2. Database Migration Failure
**Error:** `sqlalchemy.exc.OperationalError: no such table` or Alembic errors.
**Resolution:** 
Ensure your `DATABASE_URL` is correct. If the schema is corrupted locally, you can delete `knowledge_factory.db` and recreate it:
```bash
rm knowledge_factory.db
python create_tables.py
python seed_db.py
```

### 3. 401 Unauthorized Errors
**Error:** Constant redirects to login or API requests failing with 401.
**Resolution:**
*   Ensure cookies are allowed in your browser (the refresh token is an `httpOnly` cookie).
*   If testing via Postman, ensure you are manually passing the Bearer token.
*   Check if `JWT_SECRET_KEY` matches between environments if running multiple services.

### 4. Blank/White Screen on Frontend
**Error:** React app loads but shows nothing.
**Resolution:**
Check the browser console (F12). 
*   If `VITE_API_URL` is missing, API calls will fail. Ensure `.env` exists in `app/`.
*   Check for unhandled JavaScript exceptions regarding routing roles.

### 5. Missing Environment Variables
**Error:** Application crashes on startup with `pydantic.error_wrappers.ValidationError`.
**Resolution:**
Check your `.env` file against `.env.example`. Required variables like `OPENROUTER_API_KEY` must be populated.

### 6. Assessment / Code Execution Failures
**Error:** Code evaluation returns 500 or timeout.
**Resolution:**
*   Ensure the Piston service (`SANDBOX_URL`) is accessible. 
*   If running locally, ensure the Piston docker container is running.
*   Check the backend logs for specific stderr output from the execution engine.

### 7. Proctoring WebSocket Drops
**Error:** WebSocket closes immediately with code 4003 or similar.
**Resolution:**
*   Ensure the `token` query parameter is passed in the WS URL.
*   Ensure the `PROCTORING_JWT_SECRET` is consistent.
*   Check if Nginx is configured to handle `Upgrade` headers for WebSockets.

### 8. Module Import Errors
**Error:** `ModuleNotFoundError: No module named 'app.features...'`
**Resolution:**
Ensure you are running commands from the correct directory (the parent of `app/`, not inside `app/` itself) and that your virtual environment is activated. Run the application as a module: `python -m uvicorn app.main:app`.
