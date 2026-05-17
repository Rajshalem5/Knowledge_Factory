# Environment Management

## Three Environments

| Environment | Purpose | URL | Database |
|-------------|---------|-----|----------|
| Development | Local dev, feature building | http://localhost:8000 | SQLite (`knowledge_factory.db`) |
| Staging | Pre-production testing | https://staging.knowledge-factory.com | Supabase staging DB |
| Production | Live users | https://knowledge-factory.com | Supabase production DB |

## Environment Files

```
backend/
  .env           ← LOCAL dev (committed, no real secrets)
  .env.dev       ← Development template
  .env.staging   ← Staging config (real staging creds)
  .env.prod      ← Production config (real prod creds, .gitignore'd)
```

## Switching Environments

```bash
# Development (default)
source backend/.env  # or let pydantic read .env

# Staging
cp backend/.env.staging backend/.env && uvicorn app.main:app --reload

# Production
cp backend/.env.prod backend/.env && uvicorn app.main:app --workers 4
```

## Key Differences

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| DEBUG | true | false | false |
| CORS_ORIGINS | localhost:5173 | staging domain | production domain |
| SECURE_COOKIES | false | true | true |
| MAINTENANCE_MODE | false | false | false (flip to true for deploys) |
| SENTRY_DSN | empty | sentry staging | sentry production |
| LOGIN_RATE_LIMIT | 5/15min | 5/15min | 3/15min |

## Deployment Checklist

Before deploying to production:
1. Copy `.env.prod` to `.env` on the server
2. Verify DATABASE_URL points to production Supabase
3. Set MAINTENANCE_MODE=true
4. Run migration: `alembic upgrade head`
5. Deploy code
6. Set MAINTENANCE_MODE=false
7. Monitor logs for first 10 minutes