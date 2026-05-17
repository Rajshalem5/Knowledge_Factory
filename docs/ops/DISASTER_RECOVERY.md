# Disaster Recovery Runbook for Knowledge Factory

## Scenario 1: Database Corruption / Data Loss

### Step 1: Identify the problem
- Check `/health` endpoint returns 500
- Check logs: `tail -100 logs/knowledge_factory.log`
- Verify SQLite file exists and is readable: `ls -lh backend/knowledge_factory.db`

### Step 2: Restore from backup
- List available backups: `ls -lh /mnt/hermes-shared/backups/knowledge-factory/`
- Pick the most recent backup before the incident
- Stop the server: `pkill -f "uvicorn app.main:app"` or `pm2 stop all`
- Replace corrupted DB:
  ```bash
  cp /mnt/hermes-shared/backups/knowledge-factory/kf_YYYYMMDD_HHMMSS.db backend/knowledge_factory.db
  ```
- Restart server
- Verify: `curl http://localhost:8000/health`

### Step 3: If no local backups exist (use Supabase point-in-time recovery)
- Go to Supabase Dashboard > your project > Database > Point-in-time recovery
- Create a new branch from 5 minutes ago
- Export data: `pg_dump "postgresql://user:pass@host:5432/db" > backup.sql`
- Convert to SQLite if needed (for local dev)

---

## Scenario 2: Hosting Provider Outage (Supabase / Railway / Replit)

### Step 1: Verify it's not your code
- `curl https://your-api/health` — if this fails, check the hosting status page
- Check Supabase status: https://status.supabase.com

### Step 2: Fallback to local development
```bash
cd backend
# Switch to SQLite for local dev
# Edit .env: DATABASE_URL=sqlite+aiosqlite:///./knowledge_factory.db
uvicorn app.main:app --reload --port 8000
```

### Step 3: Expose via NGROK fallback
```bash
ngrok http 8000 --log=stdout > /tmp/ngrok.log &
# Read ngrok URL from logs and update frontend VITE_API_URL
```

### Step 4: For production, set up multi-region read replica
- Supabase: enable read replicas in your project settings
- Update `DATABASE_URL` to use replica for reads, primary for writes

---

## Scenario 3: Credential Leak (API key, JWT secret, DB password exposed)

### Step 1: Immediate rotation
- Generate new JWT_SECRET_KEY:
  ```python
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
- Update `backend/.env` with new key
- Rotate AI_API_KEY in AI service dashboard
- Rotate Supabase DB password

### Step 2: Check what was exposed
- Search git history: `git log -p --all -S "your-exposed-key"`
- If committed to git, force-push clean history (ask Shalem first)

### Step 3: Notify affected users
- If user data was at risk, notify within 72 hours per GDPR

---

## Scenario 4: Server Crash / OOM

### Symptoms
- 502 Bad Gateway
- `/health` returns 503
- `dmesg | tail` shows OOM killer

### Recovery
```bash
# Check memory usage
free -h
# Check disk space
df -h
# Check process memory
ps aux --sort=-%mem | head -10

# Restart with memory limits
uvicorn app.main:app --workers 2 --limit-concurrency 50
```

### Prevention
- Set `DB_POOL_SIZE=10` and `DB_MAX_OVERFLOW=5` in config
- Add swap: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
- Monitor with UptimeRobot (see docs/ops/UPTIME_MONITORING.md)

---

## Contacts
- **Shalem Raj** (Owner): @shalem on Telegram
- **Supabase Support**: https://supabase.com/dashboard/support
- **Sentry**: https://sentry.io/organizations/your-org/issues