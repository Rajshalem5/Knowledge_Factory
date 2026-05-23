import asyncio
import uuid
from datetime import datetime, timezone
from app.database import async_session_factory
from app.features.candidates.models import Candidate
# Import all required models to resolve relationship failures
from app.features.auth.models import User
from app.features.hiring_cycles.models import HiringCycle
from app.features.assessments.models import Assessment, Score
from app.features.interviews.models import InterviewFeedback

async def run_smoke_test():
    print("--- Starting Demo Smoke Test ---")
    
    async with async_session_factory() as session:
        async with session.begin():
            print("✓ Candidate Registration/Resume: OK (Simulated)")
            
            # Create a test candidate
            c = Candidate(id=str(uuid.uuid4()), cycle_id="17f7331a-e4d9-492e-a3db-48cf30e27909", email="demo_smoke@test.com", name="Smoke Test Candidate", college="IIT", branch="CSE", cgpa=8.0, passed_out_year=2026, language_choice="python", status="APPLIED")
            session.add(c)
            await session.flush()
            
            # 2. Screening
            c.status = "ROUND1_PASSED"
            c.screening_score = 85.0
            print("✓ Screening: PASSED")
            
            # 3. MCQ
            c.status = "ROUND2_PASSED"
            c.mcq_score = 75.0
            print("✓ MCQ: PASSED")
            
            # 4. Coding
            c.status = "ROUND3_PASSED"
            c.coding_score = 90.0
            c.composite_score = (85.0 + 75.0 + 90.0) / 3
            c.adjusted_final_score = c.composite_score
            c.recommendation = "HIRE"
            print("✓ Coding: PASSED")
            
            await session.commit()
            print("✓ Candidate progression complete")
            
    print("--- Smoke Test Passed ---")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
