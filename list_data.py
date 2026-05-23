import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath("backend"))

# pyrefly: ignore [missing-import]
from app.database import async_session_factory
from sqlalchemy import text

async def list_data():
    async with async_session_factory() as session:
        print("--- USERS ---")
        res = await session.execute(text("SELECT email, role FROM users"))
        for row in res:
            print(f"{row[0]} - {row[1]}")
            
        print("\n--- CANDIDATES ---")
        res2 = await session.execute(text("SELECT email, status FROM candidates"))
        for row in res2:
            print(f"{row[0]} - {row[1]}")

if __name__ == "__main__":
    asyncio.run(list_data())
