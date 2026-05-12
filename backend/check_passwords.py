"""Test login with existing users."""
import asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.security import verify_password, hash_password

from app.database import async_session_factory
from sqlalchemy import select
from app.features.candidates.models import Candidate
from app.features.auth.models import User

async def check_passwords():
    async with async_session_factory() as session:
        # Check users
        for email in ['hr@knowledgefactory.com', 'admin@knowledgefactory.io']:
            stmt = select(User).where(User.email == email)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if user:
                print(f"User {email}: hash={user.password_hash[:30]}...")
                pw_check = verify_password("Hr@12345" if "hr" in email else "Admin@12345", user.password_hash)
                print(f"  Password check: {pw_check}")
            else:
                print(f"User {email}: NOT FOUND")
        
        # Check candidates
        for email in ['alice@test.com', 'bob@test.com']:
            stmt = select(Candidate).where(Candidate.email == email)
            res = await session.execute(stmt)
            c = res.scalar_one_or_none()
            if c:
                print(f"Candidate {email}: status={c.status}, has_hash={'yes' if c.password_hash else 'no'}")
                if c.password_hash:
                    pw_check = verify_password("password123", c.password_hash)
                    print(f"  Password check: {pw_check}")

asyncio.run(check_passwords())
