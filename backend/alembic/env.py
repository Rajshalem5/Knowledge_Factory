"""Alembic environment configuration for async migrations."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.database import Base

# Import all models here so Alembic can detect them for autogenerate.
# Each import registers the model's table with Base.metadata.
from app.features.auth.models import Tenant, User  # noqa: F401
from app.features.hiring_cycles.models import HiringCycle  # noqa: F401
from app.features.candidates.models import Candidate  # noqa: F401
from app.features.assessments.models import Assessment, Submission, Score  # noqa: F401
from app.features.proctoring.models import ProctoringRecord  # noqa: F401
from app.features.interviews.models import InterviewFeedback  # noqa: F401
from app.features.audit.models import AuditLog  # noqa: F401
from app.features.notifications.models import EmailLog  # noqa: F401
from app.features.analytics.models import AIGenerationLog  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with the value from Settings, so we don't
# duplicate the connection string in alembic.ini.
config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL script generation)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations — delegates to async."""
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
