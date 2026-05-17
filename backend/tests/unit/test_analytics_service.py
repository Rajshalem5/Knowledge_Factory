"""Unit tests for the AnalyticsService.

Uses an isolated SQLite in-memory database (separate from conftest's session-scoped DB)
so tests are deterministic regardless of integration test side effects.
"""

import asyncio
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.core.enums import CandidateStatus
from app.features.analytics.service import AnalyticsService
from app.features.analytics.schemas import FunnelResponse, DashboardResponse
from app.features.assessments.models import Score
from app.features.hiring_cycles.models import HiringCycle
from app.features.candidates.models import Candidate

# Isolated in-memory SQLite — no cross-test contamination
_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
_SessionFactory = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def setup_tables():
    """Create tables once per test session."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(setup_tables) -> AsyncSession:
    """Provide a clean session per test, rolled back after."""
    async with _SessionFactory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.mark.asyncio
async def test_get_hiring_funnel_empty(db: AsyncSession):
    """Test: Funnel with no candidates returns zeros."""
    service = AnalyticsService(db)
    result = await service.get_hiring_funnel()
    assert isinstance(result, FunnelResponse)
    assert result.applied == 0
    assert result.eligible == 0
    assert result.assessed == 0
    assert result.interviewed == 0
    assert result.selected == 0


@pytest.mark.asyncio
async def test_get_hiring_funnel_with_candidates(db: AsyncSession):
    """Test: Funnel correctly counts candidates by stage."""
    cycle = HiringCycle(
        name="Test Cycle",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status="ACTIVE",
        eligibility_config={"min_cgpa": 6.0, "allowed_branches": ["CSE"]},
    )
    db.add(cycle)
    await db.flush()

    candidates_data = [
        {"name": "Applied1", "email": "a1@test.com", "college": "Uni A", "branch": "CSE",
         "cgpa": 7.0, "passed_out_year": 2026, "language_choice": "python", "password_hash": "hash", "status": CandidateStatus.APPLIED},
        {"name": "Applied2", "email": "a2@test.com", "college": "Uni A", "branch": "CSE",
         "cgpa": 7.5, "passed_out_year": 2026, "language_choice": "java", "password_hash": "hash", "status": CandidateStatus.ROUND1_REVIEW},
        {"name": "Eligible1", "email": "e1@test.com", "college": "Uni B", "branch": "ECE",
         "cgpa": 8.0, "passed_out_year": 2026, "language_choice": "python", "password_hash": "hash", "status": CandidateStatus.ROUND1_PASSED},
        {"name": "Assessed1", "email": "as1@test.com", "college": "Uni C", "branch": "IT",
         "cgpa": 8.5, "passed_out_year": 2026, "language_choice": "javascript", "password_hash": "hash", "status": CandidateStatus.ROUND2_IN_PROGRESS},
        {"name": "Interviewed1", "email": "i1@test.com", "college": "Uni D", "branch": "CSE",
         "cgpa": 9.0, "passed_out_year": 2026, "language_choice": "python", "password_hash": "hash", "status": CandidateStatus.INTERVIEW_SCHEDULED},
        {"name": "Selected1", "email": "s1@test.com", "college": "Uni E", "branch": "CSE",
         "cgpa": 9.5, "passed_out_year": 2026, "language_choice": "go", "password_hash": "hash", "status": CandidateStatus.SELECTED},
    ]

    for cd in candidates_data:
        c = Candidate(cycle_id=cycle.id, **cd)
        db.add(c)
    await db.flush()

    service = AnalyticsService(db)
    result = await service.get_hiring_funnel()

    assert result.applied == 2        # APPLIED + ROUND1_REVIEW
    assert result.eligible == 1       # ROUND1_PASSED
    assert result.assessed == 1       # ROUND2_IN_PROGRESS
    # interviewed includes INTERVIEW_SCHEDULED, INTERVIEW_COMPLETED, SELECTED
    # we have INTERVIEW_SCHEDULED=1, SELECTED=1 -> interviewed = 2
    assert result.interviewed == 2
    assert result.selected == 1       # SELECTED


@pytest.mark.asyncio
async def test_get_hiring_funnel_with_branch_filter(db: AsyncSession):
    """Test: Funnel respects the branch filter."""
    cycle = HiringCycle(
        name="Filter Cycle",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status="ACTIVE",
        eligibility_config={"min_cgpa": 6.0, "allowed_branches": ["CSE", "ECE"]},
    )
    db.add(cycle)
    await db.flush()

    candidates = [
        {"name": "CSE Applied", "email": "cse@test.com", "college": "Uni A", "branch": "CSE",
         "cgpa": 7.5, "passed_out_year": 2026, "language_choice": "python", "password_hash": "hash", "status": CandidateStatus.APPLIED},
        {"name": "CSE Applied2", "email": "cse2@test.com", "college": "Uni A", "branch": "CSE",
         "cgpa": 7.5, "passed_out_year": 2026, "language_choice": "java", "password_hash": "hash", "status": CandidateStatus.ROUND1_REVIEW},
        {"name": "ECE Applied", "email": "ece@test.com", "college": "Uni A", "branch": "ECE",
         "cgpa": 8.0, "passed_out_year": 2026, "language_choice": "python", "password_hash": "hash", "status": CandidateStatus.APPLIED},
        {"name": "Civil Applied", "email": "civil@test.com", "college": "Uni B", "branch": "CIVIL",
         "cgpa": 7.0, "passed_out_year": 2026, "language_choice": "c++", "password_hash": "hash", "status": CandidateStatus.APPLIED},
    ]

    for cd in candidates:
        c = Candidate(cycle_id=cycle.id, **cd)
        db.add(c)
    await db.flush()

    service = AnalyticsService(db)
    # Filter by CSE only
    result = await service.get_hiring_funnel(branch="CSE")

    assert result.applied == 2   # only 2 CSE candidates counted in applied stage
    assert result.eligible == 0


@pytest.mark.asyncio
async def test_get_dashboard_empty(db: AsyncSession):
    """Test: Dashboard with no candidates returns zeros."""
    service = AnalyticsService(db)
    result = await service.get_dashboard()

    assert isinstance(result, DashboardResponse)
    assert result.total_candidates == 0
    assert result.selected_count == 0
    assert result.select_rate == 0.0
    assert result.avg_cgpa == 0.0
    assert result.status_breakdown == {}
    assert result.pass_rate_per_round == []
    assert result.college_breakdown == []
    assert result.branch_performance == []
    assert result.proctoring_violations == []


@pytest.mark.asyncio
async def test_get_dashboard_with_data(db: AsyncSession):
    """Test: Dashboard returns aggregated data correctly."""
    cycle = HiringCycle(
        name="Dash Cycle",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status="ACTIVE",
    )
    db.add(cycle)
    await db.flush()

    c1 = Candidate(
        cycle_id=cycle.id, name="C1", email="c1@test.com", college="Uni A",
        branch="CSE", cgpa=8.0, passed_out_year=2026, language_choice="python",
        password_hash="hash",
        status=CandidateStatus.SELECTED,
    )
    c2 = Candidate(
        cycle_id=cycle.id, name="C2", email="c2@test.com", college="Uni B",
        branch="ECE", cgpa=7.5, passed_out_year=2026, language_choice="java",
        password_hash="hash",
        status=CandidateStatus.APPLIED,
    )
    db.add_all([c1, c2])
    await db.flush()

    # Add a score record for pass rate
    score = Score(
        candidate_id=c1.id, round="ROUND_2",
        correctness=85, quality=80, design=75, edge_cases=80, efficiency=90,
        mcq_total=40, weighted_total=85.0, verdict="PASS",
    )
    db.add(score)
    await db.flush()

    service = AnalyticsService(db)
    result = await service.get_dashboard()

    assert result.total_candidates == 2
    assert result.selected_count == 1
    assert result.select_rate == 50.0  # 1/2 * 100
    assert result.avg_cgpa == 7.75     # (8.0 + 7.5) / 2
    assert len(result.status_breakdown) == 2

    # Pass rate for ROUND_2: 1 PASS out of 1 total
    assert len(result.pass_rate_per_round) == 1
    assert result.pass_rate_per_round[0].round == "ROUND_2"
    assert result.pass_rate_per_round[0].pass_rate == 100.0

    # Branch performance
    assert len(result.branch_performance) > 0
