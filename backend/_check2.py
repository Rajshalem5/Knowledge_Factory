"""Dump full candidate info from DB."""
import sys
sys.path.insert(0, '.')
import asyncio
from sqlalchemy import select
from app.database import async_session_factory
from app.core.security import verify_password
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.features.auth.models import User

async def check():
    async with async_session_factory() as session:
        async with session.begin():
            result = await session.execute(select(Candidate))
            candidates = result.scalars().all()
            print(f"Candidates: {len(candidates)}")
            for c in candidates:
                # Try common passwords
                for pw in ["Candidate@123", "password", "Password@123", "candidate123", "Test@123"]:
                    if c.password_hash and verify_password(pw, c.password_hash):
                        print(f"  {c.email} -> MATCHES password='{pw}' status={c.status}")
                        break
                else:
                    print(f"  {c.email} -> no match found status={c.status}")

asyncio.run(check())
