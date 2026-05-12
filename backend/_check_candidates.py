"""Check candidates in the database."""
import asyncio
import sys
sys.path.insert(0, ".")
from app.database import async_session_factory
from app.features.candidates.models import Candidate
from sqlalchemy import select

async def check():
    async with async_session_factory() as session:
        result = await session.execute(select(Candidate))
        candidates = result.scalars().all()
        print(f"Total candidates: {len(candidates)}")
        for c in candidates:
            print(f"  ID={c.id} EMAIL={c.email} NAME={c.name} STATUS={c.status} CYCLE={c.cycle_id} CGPA={c.cgpa}")
asyncio.run(check())
