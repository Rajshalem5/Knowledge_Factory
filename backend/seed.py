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
from app.features.interviews.models import InterviewFeedback
from app.features.audit.models import AuditLog
from app.features.analytics.models import AIGenerationLog
from app.features.proctoring.models import ProctoringSession, ProctoringEvent, ProctoringEvidence, RiskSnapshot
from app.features.notifications.models import EmailLog



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
        # Clear Existing Data
        # Clear All Existing Data
        print('Clearing all existing data...')
        session.query(RiskSnapshot).delete()
        session.query(ProctoringEvidence).delete()
        session.query(ProctoringEvent).delete()
        session.query(ProctoringSession).delete()
        session.query(EmailLog).delete()
        session.query(Score).delete()
        session.query(Submission).delete()
        session.query(Assessment).delete()
        session.query(InterviewFeedback).delete()
        session.query(Candidate).delete()
        session.query(HiringCycle).delete()
        session.query(AuditLog).delete()
        session.query(AIGenerationLog).delete()
        session.query(User).delete()
        session.flush()
        print('All existing data cleared.')

        # ── Staff Users ─────────────────────────────────────────────
        staff_users = [
            {"email": "superadmin@knowledgefactory.io", "password": "Super@12345", "name": "Super Admin", "role": Role.SUPER_ADMIN},
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
                print(f"Updated staff: {su['email']} (Password: {su['password']})")
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
                print(f"Created staff: {su['email']} (Password: {su['password']})")
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
        
        # Seed test candidates
        candidates_data = [
            {"name": "Alice Sharma", "email": "alice@test.com", "password": "Welcome@123", "college": "IIT Bombay", "branch": "CSE", "cgpa": 8.7, "passed_out_year": 2026, "language_choice": "python"},
            {"name": "Bob Patel", "email": "bob@test.com", "password": "Welcome@123", "college": "NIT Trichy", "branch": "ECE", "cgpa": 7.2, "passed_out_year": 2026, "language_choice": "java"},
            {"name": "Test Candidate", "email": "candidate@test.com", "password": "Welcome@123", "college": "Test University", "branch": "CSE", "cgpa": 8.5, "passed_out_year": 2026, "language_choice": "python"},
        ]
        
        for cd in candidates_data:
            pw = cd.pop("password")
            existing = session.query(Candidate).filter(Candidate.email == cd["email"]).first()
            if existing:
                existing.password_hash = hash_password(pw)
                existing.name = cd["name"]
                existing.college = cd["college"]
                existing.branch = cd["branch"]
                existing.cgpa = cd["cgpa"]
                existing.passed_out_year = cd["passed_out_year"]
                existing.language_choice = cd["language_choice"]
                print(f"Updated candidate: {cd['email']} (Password: {pw})")
            else:
                c = Candidate(
                    cycle_id=cycle.id,
                    password_hash=hash_password(pw),
                    **cd,
                )
                session.add(c)
                print(f"Created candidate: {cd['email']} (Password: {pw})")
        
        session.commit()
        
        # ── Verify ──────────────────────────────────────────────────
        print("\nVerifying credentials...")
        for su in staff_users:
            user = session.query(User).filter(User.email == su["email"]).first()
            if user:
                ok = verify_password_test(su["password"], user.password_hash)
                print(f"  Verify {su['email']}: {'PASS' if ok else 'FAIL'}")
            else:
                print(f"  Verify {su['email']}: NOT FOUND")
        
        # Verify candidate@test.com
        test_c = session.query(Candidate).filter(Candidate.email == "candidate@test.com").first()
        if test_c:
            ok = verify_password_test("Welcome@123", test_c.password_hash)
            print(f"  Verify candidate@test.com: {'PASS' if ok else 'FAIL'}")
        
        print("\nSeed complete!")


def verify_password_test(plain_password: str, hashed_password: str) -> bool:
    """Wrapper around core.security verify_password for seed verification."""
    from app.core.security import verify_password
    return verify_password(plain_password, hashed_password)


def verify_password_test(plain_password: str, hashed_password: str) -> bool:
    """Wrapper around core.security verify_password for seed verification."""
    from app.core.security import verify_password
    return verify_password(plain_password, hashed_password)


if __name__ == "__main__":
    seed()
