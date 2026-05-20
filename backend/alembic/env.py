"""Alembic environment configuration for async migrations.

Supports both SQLite (development) and PostgreSQL (production).
SQLite migration behavior:
  - ALTER operations may be limited (SQLite has weak ALTER support)
  - Use recreate=True for complex migrations
  - Comments as needed for complex schema changes
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.database import Base

# Import all models here so Alembic can detect them for autogenerate.
from app.features.auth.models import User  # noqa: F401
from app.features.hiring_cycles.models import HiringCycle  # noqa: F401
from app.features.candidates.models import Candidate  # noqa: F401
from app.features.assessments.models import Assessment, Submission, Score  # noqa: F401
from app.features.proctoring.models import (  # noqa: F401
    ProctoringSession,
    ProctoringEvent,
    ProctoringEvidence,
    RiskSnapshot,
)
from app.features.interviews.models import InterviewFeedback  # noqa: F401
from app.features.audit.models import AuditLog  # noqa: F401
from app.features.notifications.models import EmailLog  # noqa: F401
from app.features.analytics.models import AIGenerationLog  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with the value from Settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL script generation).
    
    This is useful for:
    - Generating migration SQL without connecting to database
    - SQLite environments with limited ALTER support
    """
    url = config.get_main_option("sqlalchemy.url")
    
    # SQLite-specific configuration
    dialect_opts = {}
    if "sqlite" in url:
        dialect_opts = {
            "paramstyle": "named",
            "sqlite_include_foreign_keys": True,
        }
    else:
        dialect_opts = {"paramstyle": "named"}
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts=dialect_opts,
    )
    
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Execute migrations with the given connection."""
    is_sqlite = "sqlite" in settings.DATABASE_URL
    
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=is_sqlite,  # SQLite requires batch mode for ALTER operations
    )
    
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using an async engine."""
    is_sqlite = "sqlite" in settings.DATABASE_URL
    
    engine_config = config.get_section(config.config_ini_section, {})
    
    if is_sqlite:
        # SQLite uses NullPool by default (proper for SQLite)
        engine_config["sqlalchemy.poolclass"] = pool.NullPool
        engine_config["sqlalchemy.connect_args"] = {
            "timeout": 30,
            "check_same_thread": False,
        }
    
    connectable = async_engine_from_config(
        engine_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool if is_sqlite else pool.StaticPool,
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations."""
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
