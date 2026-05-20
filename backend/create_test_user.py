"""
Create a test candidate user for testing the assessment page.
"""

import asyncio
from datetime import date
from sqlalchemy import select

from app.database import async_session_factory
from app.core.security import hash_password
from app.core.enums import TenantStatus, CycleStatus, CandidateStatus

# Import all models to ensure relationships are configured
from app.features.auth.models import Tenant
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle


async def create_test_user():
    """Create a test candidate user."""
    
    async with async_session_factory() as session:
        try:
            # Check if tenant exists
            result = await session.execute(select(Tenant).limit(1))
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                print("Creating default tenant...")
                tenant = Tenant(
                    name="Default Org",
                    slug="default-org",
                    status=TenantStatus.ACTIVE
                )
                session.add(tenant)
                await session.flush()
            
            # Check if hiring cycle exists
            result = await session.execute(
                select(HiringCycle)
                .where(HiringCycle.tenant_id == tenant.id)
                .limit(1)
            )
            cycle = result.scalar_one_or_none()
            
            if not cycle:
                print("Creating default hiring cycle...")
                cycle = HiringCycle(
                    tenant_id=tenant.id,
                    name="Test Cycle 2026",
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 12, 31),
                    status=CycleStatus.ACTIVE,
                    eligibility_config={"min_cgpa": 7.0},
                    assessment_config={"languages": ["python", "java", "cpp"]},
                    proctoring_config={"max_warnings": 3},
                )
                session.add(cycle)
                await session.flush()
            
            # Check if test candidate already exists
            result = await session.execute(
                select(Candidate).where(Candidate.email == "candidate@test.com")
            )
            existing_candidate = result.scalar_one_or_none()
            
            if existing_candidate:
                print("\n✅ Test candidate already exists!")
                print("\nLogin credentials:")
                print("  Email: candidate@test.com")
                print("  Password: Test@123")
                print("\nGo to: http://localhost:5173/login")
                return
            
            # Create test candidate
            print("Creating test candidate...")
            candidate = Candidate(
                tenant_id=tenant.id,
                cycle_id=cycle.id,
                email="candidate@test.com",
                password_hash=hash_password("Test@123"),
                name="Test Candidate",
                phone="+1234567890",
                college="Test University",
                branch="Computer Science",
                cgpa=8.5,
                passed_out_year=2026,
                language_choice="python",
                status=CandidateStatus.ROUND2_IN_PROGRESS,
                email_verified=True,
                resume_url="",
                govt_id_url="",
                custom_fields={}
            )
            session.add(candidate)
            
            await session.commit()
            
            print("\n✅ Test candidate created successfully!")
            print("\n" + "=" * 50)
            print("LOGIN CREDENTIALS")
            print("=" * 50)
            print("Email:    candidate@test.com")
            print("Password: Test@123")
            print("=" * 50)
            print("\nSteps to test:")
            print("1. Start backend: uvicorn app.main:app --reload --port 8000")
            print("2. Start frontend: npm run dev (in app folder)")
            print("3. Go to: http://localhost:5173/login")
            print("4. Login with credentials above")
            print("5. Navigate to: http://localhost:5173/assessment")
            print("\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(create_test_user())
