# DATABASE_ACCESS Security Report

## Status: N/A (Not applicable)

## Findings

This project uses a **server-side only** database architecture:

- **ORM**: SQLAlchemy 2.0 (async) via FastAPI
- **Dev database**: SQLite (`sqlite+aiosqlite:///./knowledge_factory.db`)
- **Production database**: PostgreSQL (via `postgresql+asyncpg://`)
- **No Supabase or Firebase** — there is no client-accessible database with anon keys or RLS policies

Database tables (`users`, `candidates`, `assessments`, `submissions`, `scores`, `hiring_cycles`, `proctoring_records`, `interview_feedback`, `audit_logs`, `email_logs`, `ai_generation_logs`)

All database access is mediated through the FastAPI backend:
- Routes validate authentication via JWT middleware
- Service layer enforces role-based authorization
- SQLAlchemy ORM with parameterized queries (no raw SQL injection risk)

### What's at risk

Not applicable — there is no direct client-to-database pathway. The database is only accessible from the backend API, which has auth middleware.

### What's already secure

- SQLAlchemy ORM is used throughout (parameterized queries, no raw SQL concatenation)
- Auth middleware protects API routes
- Database is server-side only, not exposed to clients

### Recommendations

1. **[MEDIUM]** When migrating to PostgreSQL in production, use a database user with least-privilege permissions (not the schema owner) for the application connection
2. **[LOW]** Enable SQLAlchemy connection encryption (sslmode=require) for production PostgreSQL
3. **[LOW]** Consider database-level audit logging for sensitive tables
