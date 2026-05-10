"""
Debug funnel query issue directly against the real database.
"""
import asyncio
from sqlalchemy import select, func
from app.database import async_session_factory

# Import ALL models to ensure SQLAlchemy discovers them
import app.features.auth.models
import app.features.candidates.models
import app.features.hiring_cycles.models
import app.features.assessments.models
import app.features.proctoring.models
import app.features.interviews.models
import app.features.audit.models
import app.features.analytics.models

from app.features.candidates.models import Candidate
from app.core.enums import CandidateStatus

async def main():
    async with async_session_factory() as session:
        # Total candidates
        r = await session.execute(select(func.count(Candidate.id)))
        total = r.scalar()
        print(f"Total candidates in DB: {total}")

        # Check status distribution
        r = await session.execute(
            select(Candidate.status, func.count(Candidate.id))
            .group_by(Candidate.status)
        )
        print(f"\nStatus distribution:")
        for status, count in r.all():
            print(f"  {status}: {count}")

        # Test the funnel's applied query directly
        q_applied = (
            select(func.count(Candidate.id))
            .where(Candidate.status.in_([CandidateStatus.APPLIED, CandidateStatus.ROUND1_REVIEW]))
        )
        r = await session.execute(q_applied)
        applied_count = r.scalar() or 0
        print(f"\nDirect funnel 'applied' query: {applied_count}")

        # Generate raw SQL for the applied query
        from sqlalchemy.dialects import sqlite
        compiled = q_applied.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
        print(f"\nSQL: {compiled}")

        # Test applied query with name filter
        q_applied_filtered = (
            select(func.count(Candidate.id))
            .where(Candidate.status.in_([CandidateStatus.APPLIED, CandidateStatus.ROUND1_REVIEW]))
            .where(Candidate.name.ilike("%Test%"))
        )
        r = await session.execute(q_applied_filtered)
        filtered_count = r.scalar() or 0
        print(f"\nApplied + name=Test: {filtered_count}")
        compiled2 = q_applied_filtered.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
        print(f"SQL: {compiled2}")

        # Try using string values directly instead of enum members
        q_applied_str = (
            select(func.count(Candidate.id))
            .where(Candidate.status.in_(["APPLIED", "ROUND1_REVIEW"]))
        )
        r = await session.execute(q_applied_str)
        applied_str_count = r.scalar() or 0
        print(f"\nApplied query with string literals: {applied_str_count}")

        # Test eligible query
        q_eligible = (
            select(func.count(Candidate.id))
            .where(Candidate.status == CandidateStatus.ROUND1_PASSED)
        )
        r = await session.execute(q_eligible)
        eligible_count = r.scalar() or 0
        print(f"\nEligible query: {eligible_count}")

        # Test with email filter
        q_email = (
            select(func.count(Candidate.id))
            .where(Candidate.status.in_([CandidateStatus.APPLIED, CandidateStatus.ROUND1_REVIEW]))
            .where(Candidate.email == "applied@test.com")
        )
        r = await session.execute(q_email)
        email_count = r.scalar() or 0
        print(f"\nApplied + email=applied@test.com: {email_count}")

asyncio.run(main())
