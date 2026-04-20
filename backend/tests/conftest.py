"""Shared pytest fixtures for the Knowledge Factory test suite."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.main import app


# Use a separate test database to avoid polluting dev data.
TEST_DATABASE_URL = (
    "postgresql+asyncpg://kf_user:kf_password@localhost:5432/kf_test"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Create all tables before the test session and drop them after.

    This uses the ORM metadata (Base) to create tables. In a real
    project, you might use Alembic migrations instead to test the
    migration path.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a clean database session for each test.

    Each test runs inside a transaction that is rolled back at the end,
    ensuring test isolation without needing to recreate tables.
    """
    async with TestSessionFactory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for integration tests.

    Uses httpx's ASGITransport to call the FastAPI app directly,
    avoiding the overhead of a real HTTP server during tests.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
