"""Seed the live database with staff users, active cycle, and test candidates."""
import asyncio
import sys
sys.path.insert(0, ".")
from app.database import async_session_factory, Base
from sqlalchemy import create_engine as create_sync_engine
from app.core.security import hash_password, verify_password
from datetime import date
from sqlalchemy import select, delete

# Import ALL models so SQLAlchemy can resolve relationships
from app.features.auth.models import User
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.features.assessments.models import Assessment, Submission, Score
from app.features.interviews.models import InterviewFeedback
from app.features.audit.models import AuditLog
from app.features.analytics.models import AIGenerationLog
from app.features.proctoring.models import ProctoringSession, ProctoringEvent, ProctoringEvidence, RiskSnapshot
from app.features.notifications.models import EmailLog



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
            # Clear All Existing Data (Async)
            print('Clearing all existing data...')
            await session.execute(delete(RiskSnapshot))
            await session.execute(delete(ProctoringEvidence))
            await session.execute(delete(ProctoringEvent))
            await session.execute(delete(ProctoringSession))
            await session.execute(delete(EmailLog))
            await session.execute(delete(Score))
            await session.execute(delete(Submission))
            await session.execute(delete(Assessment))
            await session.execute(delete(InterviewFeedback))
            await session.execute(delete(Candidate))
            await session.execute(delete(HiringCycle))
            await session.execute(delete(AuditLog))
            await session.execute(delete(AIGenerationLog))
            await session.execute(delete(User))
            print('All existing data cleared.')

            # ── Staff Users ─────────────────────────────────────────
            staff_users = [
                {
                    "email": "admin@test.com",
                    "password": "Test@123",
                    "name": "Admin User",
                    "role": "ADMIN",
                },
                {
                    "email": "hr@test.com",
                    "password": "Test@123",
                    "name": "HR Manager",
                    "role": "HR",
                },
                {
                    "email": "interviewer@test.com",
                    "password": "Test@123",
                    "name": "Interviewer",
                    "role": "INTERVIEWER",
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

            # ── Seed Test Candidates ──────────────────────────────────
            stmt = select(Candidate).limit(1)
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if not existing:
                candidates_data = [
                    {"name": "Alice Sharma", "email": "alice@test.com", "password": "Welcome@123", "college": "IIT Bombay", "branch": "CSE", "cgpa": 8.7, "passed_out_year": 2026, "language_choice": "python"},
                    {"name": "Bob Patel", "email": "bob@test.com", "password": "Welcome@123", "college": "NIT Trichy", "branch": "ECE", "cgpa": 7.2, "passed_out_year": 2026, "language_choice": "java"},
                    {"name": "Charlie Singh", "email": "charlie@test.com", "password": "Welcome@123", "college": "DTU Delhi", "branch": "IT", "cgpa": 6.5, "passed_out_year": 2025, "language_choice": "python"},
                    {"name": "Divya Kumar", "email": "divya@test.com", "password": "Welcome@123", "college": "VIT Vellore", "branch": "CSE", "cgpa": 9.1, "passed_out_year": 2026, "language_choice": "cpp"},
                    {"name": "Esha Gupta", "email": "esha@test.com", "password": "Welcome@123", "college": "SRM Chennai", "branch": "EEE", "cgpa": 5.8, "passed_out_year": 2026, "language_choice": "python"},
                    {"name": "Farhan Qureshi", "email": "farhan@test.com", "password": "Welcome@123", "college": "BITS Pilani", "branch": "CSE", "cgpa": 8.3, "passed_out_year": 2024, "language_choice": "java"},
                    {"name": "Gauri Joshi", "email": "gauri@test.com", "password": "Welcome@123", "college": "COEP Pune", "branch": "CIVIL", "cgpa": 7.8, "passed_out_year": 2026, "language_choice": "python"},
                ]
                from app.core.security import hash_password as _hash
                for cd in candidates_data:
                    pw = cd.pop("password")
                    c = Candidate(
                        cycle_id=cycle.id,
                        password_hash=_hash(pw),
                        **cd,
                    )
                    session.add(c)
                print(f"[seed] Created {len(candidates_data)} test candidates")
            else:
                print(f"[seed] Test candidates already exist, skipping")

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
