"""Shared pytest fixtures for the Knowledge Factory test suite.

Uses SQLite by default (set TEST_DATABASE_URL env var to override for CI).
Each test gets its own transaction that is rolled back at the end,
ensuring complete test isolation while keeping HTTP requests within a
test visible to each other via flush().
"""

import asyncio
import os
from datetime import date
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.core.security import hash_password
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.features.auth.models import User

# Use SQLite for local dev; override via env var in CI
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite://",
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
    Also seeds an admin user + active hiring cycle for auth-dependent tests.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed data
    async with TestSessionFactory() as session:
        admin = User(
            email="admin@knowledgefactory.io",
            password_hash=hash_password("Admin@12345"),
            name="Admin User",
            role="SUPER_ADMIN",
            status="ACTIVE",
        )
        session.add(admin)

        hr_user = User(
            email="hr@knowledgefactory.com",
            password_hash=hash_password("Hr@12345"),
            name="HR Manager",
            role="HR",
            status="ACTIVE",
        )
        session.add(hr_user)

        cycle = HiringCycle(
            name="Test Cycle",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status="ACTIVE",
            eligibility_config={"min_cgpa": 6.0, "allowed_branches": ["CSE", "ECE", "IT", "EEE"]},
        )
        session.add(cycle)
        await session.flush()

        # Seed test candidates in APPLIED status for screening tests
        candidates_data = [
            {"name": "Test Candidate Applied", "email": "applied@test.com", "college": "Test Uni", "branch": "CSE", "cgpa": 8.5, "passed_out_year": 2026, "language_choice": "python", "status": "APPLIED"},
            {"name": "Low CGPA Candidate", "email": "lowcgpa@test.com", "college": "Test Uni", "branch": "CSE", "cgpa": 5.5, "passed_out_year": 2026, "language_choice": "java", "status": "APPLIED"},
            {"name": "Wrong Branch Candidate", "email": "wrongbranch@test.com", "college": "Other Uni", "branch": "CIVIL", "cgpa": 7.5, "passed_out_year": 2026, "language_choice": "python", "status": "APPLIED"},
        ]
        for cd in candidates_data:
            c = Candidate(
                cycle_id=cycle.id, 
                password_hash=hash_password("Welcome@123"),
                **cd
            )
            session.add(c)

        await session.commit()

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
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for integration tests.

    Uses httpx's ASGITransport to call the FastAPI app directly,
    with get_db dependency overridden to share the test's db_session.
    Changes made by HTTP requests within a test are visible to subsequent
    requests (via flush) but rolled back at the end of the test.
    """
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
        # Expire all ORM objects after each request so subsequent requests
        # within the same test transaction get fresh data (including newly
        # added relationships like interview_feedback, assessments, etc.)
        db_session.expire_all()

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)
