"""Check database state - import ALL models first."""
import asyncio
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./knowledge_factory.db"

# Import ALL models so SQLAlchemy discovers relationships
import app.features.auth.models
import app.features.candidates.models
import app.features.hiring_cycles.models
import app.features.assessments.models
import app.features.proctoring.models
import app.features.interviews.models
import app.features.audit.models
import app.features.analytics.models

from app.database import async_session_factory
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from sqlalchemy import select, func

async def check():
    async with async_session_factory() as session:
        # Check hiring cycles
        stmt = select(HiringCycle)
        res = await session.execute(stmt)
        cycles = res.scalars().all()
        print('Hiring Cycles:')
        for c in cycles:
            print(f'  {c.id}: {c.name}, status={c.status}, config={c.eligibility_config}')
        
        # Count candidates by status
        stmt = select(Candidate.status, func.count(Candidate.id)).group_by(Candidate.status)
        res = await session.execute(stmt)
        rows = res.all()
        print('\nCandidates by status:')
        for s, c in rows:
            print(f'  {s}: {c}')
        total = sum(c for _, c in rows)
        print(f'  Total: {total}')
        
        # Show some candidates
        stmt2 = select(Candidate).limit(10)
        res2 = await session.execute(stmt2)
        cands = res2.scalars().all()
        print('\nSample candidates:')
        for c in cands:
            print(f'  {c.name[:20]:20s} status={str(c.status):20s} cgpa={c.cgpa} branch={c.branch} year={c.passed_out_year}')

asyncio.run(check())
