"""
Database setup using SQLAlchemy 2.0 async engine and session management.

This module provides:
1. An async engine bound to PostgreSQL via asyncpg
2. A declarative base for all ORM models
3. An async session factory (async_sessionmaker)
4. A FastAPI dependency that yields a database session per request

All models should inherit from `Base` so Alembic can auto-detect them.
The session is automatically committed or rolled back depending on whether
an exception propagates out of the request handler.
"""

import uuid
from typing import Any, AsyncGenerator

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


# ── Portable UUID type (works on SQLite + PostgreSQL) ───────────────
class PortableUUID(TypeDecorator):
    """UUID stored as String(36) on all dialects, returned as Python uuid.UUID."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect=None):
        return str(value) if value else None

    def process_result_value(self, value: Any, dialect=None):
        return uuid.UUID(value) if value else None


# Convenience factory: PortableUUID(primary_key=True, default=uuid.uuid4)
def portable_uuid_col(**kwargs):
    return mapped_column(PortableUUID, **kwargs)


# ── Engine ─────────────────────────────────────────────────────────
# The engine is created once at module import time using settings from
# config.py. asyncpg is the driver (fast, pure-Python async PostgreSQL).


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
)

# ── Session Factory ────────────────────────────────────────────────
# Each call to async_session_factory() produces a new AsyncSession.
# We use class-based sessionmaker so the dependency can type-hint it.
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep objects accessible after commit
)


# ── Declarative Base ───────────────────────────────────────────────
# All ORM models inherit from this class. It provides the metadata
# object that Alembic reads to generate migrations.
class Base(DeclarativeBase):
    """Base class for all Knowledge Factory ORM models."""
    pass


# ── FastAPI Dependency ─────────────────────────────────────────────
# ── Test Database ──────────────────────────────────────────────────
def create_test_database() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh in-memory SQLite test database with all tables and seed data."""
    import asyncio
    from datetime import date
    from sqlalchemy import create_engine as create_sync_engine
    from app.core.security import hash_password

    test_db_url = "sqlite+aiosqlite://"
    test_engine = create_async_engine(test_db_url, echo=False)
    test_session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async def _init():
        from app.features.auth.models import User
        from app.features.candidates.models import Candidate
        from app.features.hiring_cycles.models import HiringCycle
        from app.features.assessments.models import Assessment, Submission, Score
        from app.features.proctoring.models import ProctoringRecord
        from app.features.interviews.models import InterviewFeedback
        from app.features.audit.models import AuditLog
        from app.features.analytics.models import AIGenerationLog

        # Create all tables
        sync_engine = create_sync_engine("sqlite://")
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()

        async with test_session_factory() as session:
            # Seed admin user
            admin_user = User(
                email="admin@knowledgefactory.io",
                password_hash=hash_password(settings.SEED_ADMIN_PASSWORD or "Admin@12345"),
                name="Admin User",
                role="SUPERADMIN",
                status="ACTIVE",
            )
            session.add(admin_user)

            # Seed HR user
            hr_user = User(
                email="hr@knowledgefactory.com",
                password_hash=hash_password(settings.SEED_HR_PASSWORD or "Hr@12345"),
                name="HR Manager",
                role="HR",
                status="ACTIVE",
            )
            session.add(hr_user)

            # Seed a default active hiring cycle
            cycle = HiringCycle(
                name="Test Cycle",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                status="ACTIVE",
                eligibility_config={"min_cgpa": 6.0, "allowed_branches": ["CSE", "ECE", "IT", "EEE"]},
            )
            session.add(cycle)
            await session.flush()

            # Seed test candidates (in APPLIED status for screening tests)
            candidates_data = [
                {"name": "Test Candidate Applied", "email": "applied@test.com", "college": "Test Uni", "branch": "CSE", "cgpa": 8.5, "passed_out_year": 2026, "language_choice": "python", "status": "APPLIED"},
                {"name": "Low CGPA Candidate", "email": "lowcgpa@test.com", "college": "Test Uni", "branch": "CSE", "cgpa": 5.5, "passed_out_year": 2026, "language_choice": "java", "status": "APPLIED"},
                {"name": "Wrong Branch Candidate", "email": "wrongbranch@test.com", "college": "Other Uni", "branch": "CIVIL", "cgpa": 7.5, "passed_out_year": 2026, "language_choice": "python", "status": "APPLIED"},
            ]
            for cd in candidates_data:
                c = Candidate(cycle_id=cycle.id, **cd)
                session.add(c)

            await session.commit()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_init())
    loop.close()

    # Yield session for testing
    async def _get_session():
        async with test_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    gen = _get_session()
    try:
        loop = asyncio.new_event_loop()
        session = loop.run_until_complete(gen.__anext__())
        yield session
    except StopAsyncIteration:
        pass
    finally:
        loop.run_until_complete(gen.aclose())
        loop.close()
        asyncio.set_event_loop(asyncio.new_event_loop())


def cleanup_test_database():
    """Placeholder for test database cleanup."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a database session for the lifetime of a single request.

    Usage in a route handler:
        @router.get("/candidates")
        async def list_candidates(db: AsyncSession = Depends(get_db)):
            ...

    The session is committed if the handler completes without exception.
    On exception, the session is rolled back. Either way, the session
    is closed when the generator resumes after the yield.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
