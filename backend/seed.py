"""Seed script to create initial data for development."""
import asyncio
import sys
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base
from app.core.enums import Role, UserStatus, CycleStatus
from app.core.security import hash_password
from app.features.auth.models import User
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.features.assessments.models import Assessment, Submission, Score
from app.features.proctoring.models import ProctoringRecord
from app.features.interviews.models import InterviewFeedback
from app.features.audit.models import AuditLog
from app.features.analytics.models import AIGenerationLog


def seed():
    """Create initial admin user, all staff roles, active hiring cycle, and test candidates."""
    # Get sync engine for seeding
    db_url = settings.DATABASE_URL
    if "aiosqlite" in db_url:
        db_url = db_url.replace("+aiosqlite", "")
    elif "asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")
    
    engine = create_engine(db_url)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    with Session(engine) as session:
        # ── Staff Users ─────────────────────────────────────────────
        staff_users = [
            {"email": "superadmin@knowledgefactory.io", "password": "Super@12345", "name": "Super Admin", "role": Role.SUPERADMIN},
            {"email": "admin@knowledgefactory.io", "password": "admin123", "name": "Admin User", "role": Role.ADMIN},
            {"email": "hr@knowledgefactory.io", "password": "Hr@12345", "name": "HR Manager", "role": Role.HR},
            {"email": "interviewer@knowledgefactory.io", "password": "Interview@12345", "name": "Interviewer", "role": Role.INTERVIEWER},
        ]
        
        created_by = None
        for su in staff_users:
            existing = session.query(User).filter(User.email == su["email"]).first()
            if existing:
                existing.password_hash = hash_password(su["password"])
                existing.name = su["name"]
                existing.role = su["role"]
                existing.status = UserStatus.ACTIVE
                print(f"Updated staff: {su['email']} / {su['password']}")
                if su["role"] == Role.ADMIN:
                    created_by = existing
            else:
                user = User(
                    email=su["email"],
                    password_hash=hash_password(su["password"]),
                    name=su["name"],
                    role=su["role"],
                    status=UserStatus.ACTIVE,
                )
                session.add(user)
                session.flush()
                print(f"Created staff: {su['email']} / {su['password']}")
                if su["role"] == Role.ADMIN:
                    created_by = user
        
        if not created_by:
            # Fallback: pick any admin
            created_by = session.query(User).filter(User.role == Role.ADMIN).first()
        
        # Check if active hiring cycle exists
        cycle = session.query(HiringCycle).filter(HiringCycle.status == CycleStatus.ACTIVE).first()
        if not cycle:
            cycle = HiringCycle(
                name="Campus Hiring 2026",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=90),
                status=CycleStatus.ACTIVE,
                eligibility_config={
                    "min_cgpa": 6.0,
                    "allowed_branches": ["CSE", "ECE", "IT", "EEE"],
                    "passed_out_years": [2025, 2026],
                },
                assessment_config={
                    "duration_minutes": 120,
                    "languages": ["python", "javascript", "java", "cpp"],
                    "proctoring_enabled": True,
                },
                proctoring_config={
                    "max_warnings": 3,
                    "tab_switch_limit": 5,
                    "webcam_required": True,
                },
                created_by=created_by.id if created_by else None,
            )
            session.add(cycle)
            session.flush()
            print("Created active hiring cycle: Campus Hiring 2026")
        else:
            print("Active hiring cycle already exists")
        
        # Seed test candidates if none exist
        existing_candidate = session.query(Candidate).first()
        if not existing_candidate:
            candidates_data = [
                {"name": "Alice Sharma", "email": "alice@test.com", "password": "Candidate@123", "college": "IIT Bombay", "branch": "CSE", "cgpa": 8.7, "passed_out_year": 2026, "language_choice": "python"},
                {"name": "Bob Patel", "email": "bob@test.com", "password": "Candidate@123", "college": "NIT Trichy", "branch": "ECE", "cgpa": 7.2, "passed_out_year": 2026, "language_choice": "java"},
                {"name": "Charlie Singh", "email": "charlie@test.com", "password": "Candidate@123", "college": "DTU Delhi", "branch": "IT", "cgpa": 6.5, "passed_out_year": 2025, "language_choice": "python"},
                {"name": "Divya Kumar", "email": "divya@test.com", "password": "Candidate@123", "college": "VIT Vellore", "branch": "CSE", "cgpa": 9.1, "passed_out_year": 2026, "language_choice": "cpp"},
                {"name": "Esha Gupta", "email": "esha@test.com", "password": "Candidate@123", "college": "SRM Chennai", "branch": "EEE", "cgpa": 5.8, "passed_out_year": 2026, "language_choice": "python"},
            ]
            for cd in candidates_data:
                pw = cd.pop("password")
                c = Candidate(
                    cycle_id=cycle.id,
                    password_hash=hash_password(pw),
                    **cd,
                )
                session.add(c)
            print(f"Created {len(candidates_data)} test candidates (password: Candidate@123)")
        else:
            print("Test candidates already exist")
        
        session.commit()
        
        # ── Verify ──────────────────────────────────────────────────
        for su in staff_users:
            user = session.query(User).filter(User.email == su["email"]).first()
            if user:
                ok = verify_password_test(su["password"], user.password_hash)
                print(f"  Verify {su['email']}: {'PASS' if ok else 'FAIL'}")
            else:
                print(f"  Verify {su['email']}: NOT FOUND")
        
        print("Seed complete!")


def verify_password_test(plain_password: str, hashed_password: str) -> bool:
    """Wrapper around core.security verify_password for seed verification."""
    from app.core.security import verify_password
    return verify_password(plain_password, hashed_password)


if __name__ == "__main__":
    seed()
