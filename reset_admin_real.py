import asyncio
import sys
import os
from app.database import async_session_factory
from sqlalchemy import text
from app.core.security import hash_password

async def reset_pass():
    async with async_session_factory() as session:
        pwd = hash_password("Welcome@123")
        await session.execute(text(f"UPDATE users SET password_hash = '{pwd}' WHERE email = 'admin@knowledgefactory.io'"))
        await session.execute(text(f"UPDATE users SET role = 'SUPER_ADMIN' WHERE email = 'admin@knowledgefactory.io'"))
        await session.commit()
        print("Updated admin@knowledgefactory.io with Welcome@123")

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath("backend"))
    asyncio.run(reset_pass())
