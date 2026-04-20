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

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


# ── Engine ─────────────────────────────────────────────────────────
# The engine is created once at module import time using settings from
# config.py. asyncpg is the driver (fast, pure-Python async PostgreSQL).
settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DB_ECHO,
    # Prevent SQLAlchemy from logging parameterized queries in production
    pool_pre_ping=True,  # verify connections before checkout
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
