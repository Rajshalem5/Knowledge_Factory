"""Check users in the database."""
import asyncio
import sys
sys.path.insert(0, ".")
from app.database import async_session_factory
from app.features.auth.models import User
from sqlalchemy import select

async def check():
    async with async_session_factory() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Total users: {len(users)}")
        for u in users:
            print(f"  ID={u.id} EMAIL={u.email} ROLE={u.role} NAME={u.name}")
asyncio.run(check())
