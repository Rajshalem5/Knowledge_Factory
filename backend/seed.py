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
    """Create initial admin user and active hiring cycle."""
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
        # Check if admin already exists
        admin = session.query(User).filter(User.email == "admin@knowledgefactory.io").first()
        if not admin:
            admin = User(
                email="admin@knowledgefactory.io",
                password_hash=hash_password("admin123"),
                name="Admin User",
                role=Role.ADMIN,
                status=UserStatus.ACTIVE,
            )
            session.add(admin)
            session.flush()
            print("Created admin user: admin@knowledgefactory.io / admin123")
        else:
            print("Admin user already exists")
        
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
                    "branches": ["CSE", "ECE", "IT", "EEE"],
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
                created_by=admin.id,
            )
            session.add(cycle)
            session.flush()
            print("Created active hiring cycle: Campus Hiring 2026")
        else:
            print("Active hiring cycle already exists")
        
        session.commit()
        print("Seed complete!")


if __name__ == "__main__":
    seed()
