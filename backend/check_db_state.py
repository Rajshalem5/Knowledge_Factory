"""Check current database state."""
import asyncio
import sys
sys.path.insert(0, '.')
from app.database import async_session_factory
from sqlalchemy import select, func
from app.features.candidates.models import Candidate
from app.core.enums import CandidateStatus

async def check():
    async with async_session_factory() as session:
        stmt = select(Candidate.status, func.count(Candidate.id)).group_by(Candidate.status)
        res = await session.execute(stmt)
        rows = res.all()
        print('Current candidate status distribution:')
        for status, count in rows:
            print(f'  {status}: {count}')
        total = sum(c for _, c in rows) if rows else 0
        print(f'  TOTAL: {total}')

asyncio.run(check())
