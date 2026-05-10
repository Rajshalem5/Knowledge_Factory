"""Seed the live database with staff users, active cycle, and test candidates."""
import asyncio
import sys
sys.path.insert(0, ".")
from app.database import async_session_factory, Base
from sqlalchemy import create_engine as create_sync_engine
from app.core.security import hash_password, verify_password
from datetime import date
from sqlalchemy import select

# Import ALL models so SQLAlchemy can resolve relationships
from app.features.auth.models import User
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.features.assessments.models import Assessment, Submission, Score
from app.features.proctoring.models import ProctoringRecord
from app.features.interviews.models import InterviewFeedback
from app.features.audit.models import AuditLog
from app.features.analytics.models import AIGenerationLog


async def seed():
    # Create tables first (works with both SQLite and PostgreSQL)
    from app.config import settings
    db_url = settings.DATABASE_URL
    if "sqlite" in db_url:
        sync_url = db_url.replace("+aiosqlite://", "://")
        sync_engine = create_sync_engine(sync_url)
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()
        print("[seed] Tables created.")

    async with async_session_factory() as session:
        async with session.begin():
            # ── Staff Users ─────────────────────────────────────────
            staff_users = [
                {
                    "email": "hr@knowledgefactory.com",
                    "password": "Hr@12345",
                    "name": "HR Manager",
                    "role": "HR",
                },
                {
                    "email": "admin@knowledgefactory.io",
                    "password": "Admin@12345",
                    "name": "Admin User",
                    "role": "ADMIN",
                },
                {
                    "email": "ops@test.com",
                    "password": "Ops@12345",
                    "name": "Ops User",
                    "role": "SUPERADMIN",
                },
            ]
            for su in staff_users:
                stmt = select(User).where(User.email == su["email"])
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if existing:
                    existing.password_hash = hash_password(su["password"])
                    existing.name = su["name"]
                    existing.role = su["role"]
                    existing.status = "ACTIVE"
                    print(f"Updated staff: {su['email']}")
                else:
                    user = User(
                        email=su["email"],
                        password_hash=hash_password(su["password"]),
                        name=su["name"],
                        role=su["role"],
                        status="ACTIVE",
                    )
                    session.add(user)
                    print(f"Created staff: {su['email']}")

            # ── Hiring Cycle ────────────────────────────────────────
            stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE")
            cycle = (await session.execute(stmt)).scalar_one_or_none()
            if not cycle:
                cycle = HiringCycle(
                    name="Summer Internship 2026",
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 12, 31),
                    status="ACTIVE",
                    eligibility_config={"min_cgpa": 6.0, "allowed_branches": ["CSE", "ECE", "IT", "EEE"]},
                )
                session.add(cycle)
                await session.flush()
                print(f"Created hiring cycle: {cycle.id}")
            else:
                print(f"Active cycle exists: {cycle.id}")

    # ── Verify ─────────────────────────────────────────────────────
    async with async_session_factory() as session:
        async with session.begin():
            for su in staff_users:
                stmt = select(User).where(User.email == su["email"])
                user = (await session.execute(stmt)).scalar_one_or_none()
                if user:
                    ok = verify_password(su["password"], user.password_hash)
                    print(f"  Verify {su['email']}: {'PASS' if ok else 'FAIL'}")
                else:
                    print(f"  Verify {su['email']}: NOT FOUND")

            stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE")
            cycle = (await session.execute(stmt)).scalar_one_or_none()
            print(f"  Active cycle: {'FOUND' if cycle else 'MISSING'}")

    print("\nSeed complete!")


asyncio.run(seed())
