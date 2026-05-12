"""Debug: test assessment_status filter query."""
import asyncio
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, func
from app.database import Base
from app.features.assessments.models import Assessment
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.core.enums import CandidateStatus, AssessmentStatus, AssessmentRound
from app.core.security import hash_password
import uuid


async def test():
    engine = create_async_engine("sqlite+aiosqlite://", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        cycle = HiringCycle(
            name="Test", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="ACTIVE", eligibility_config={}, assessment_config={}, proctoring_config={},
        )
        session.add(cycle)
        await session.flush()

        c = Candidate(
            cycle_id=cycle.id, name="Test", email="test@test.com",
            password_hash=hash_password("Test@123"), college="Uni", branch="CSE",
            cgpa=8.0, passed_out_year=2026, language_choice="python",
            status=CandidateStatus.ROUND1_PASSED,
        )
        session.add(c)
        await session.flush()

        a = Assessment(
            id=str(uuid.uuid4()), candidate_id=c.id, round=AssessmentRound.ROUND_2,
            questions_json={}, link_token="test",
            link_expiry=date(2026, 6, 1),
            started_at=date(2026, 5, 1),
            status=AssessmentStatus.IN_PROGRESS,
        )
        session.add(a)
        await session.flush()

        # Test 1: with assessment_status filter
        q = select(Candidate.status, func.count(Candidate.id).label("count"))
        subq = select(Assessment.candidate_id).where(Assessment.status == "IN_PROGRESS")
        q = q.where(Candidate.id.in_(subq))
        q = q.group_by(Candidate.status)
        print(f"Query 1: {q}")
        result = await session.execute(q)
        rows = result.fetchall()
        print(f"Rows 1: {rows}")

        # Test 2: without filter (should return all)
        q2 = select(Candidate.status, func.count(Candidate.id).label("count"))
        q2 = q2.group_by(Candidate.status)
        print(f"Query 2: {q2}")
        result2 = await session.execute(q2)
        rows2 = result2.fetchall()
        print(f"Rows 2: {rows2}")

        # Test 3: check assessments directly
        q3 = select(Assessment)
        result3 = await session.execute(q3)
        assessments = result3.scalars().all()
        print(f"Assessments: {[(a.id, a.status, a.candidate_id) for a in assessments]}")

        # Test 4: check candidates directly
        q4 = select(Candidate)
        result4 = await session.execute(q4)
        candidates = result4.scalars().all()
        print(f"Candidates: {[(c.id, c.status) for c in candidates]}")


asyncio.run(test())
