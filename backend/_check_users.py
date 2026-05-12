import asyncio
from app.database import AsyncSessionLocal
from app.features.auth.models import User
from app.features.auth.security import verify_password
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        for u in users:
            pw_check = verify_password("admin123", u.hashed_password) if "admin" in u.email.lower() else \
                       verify_password("candidate123", u.hashed_password) if "candidate" in u.email.lower() else \
                       verify_password("hr123", u.hashed_password) if "hr@" in u.email.lower() else \
                       None
            print(f'ID={u.id} EMAIL={u.email} ROLE={u.role} PASSWORD_MATCHES={pw_check}')
asyncio.run(check())
