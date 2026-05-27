
import asyncio
import logging
from sqlalchemy import select, func
from app.database import async_session_factory
from app.features.assessments.models import Assessment
from app.core.enums import AssessmentStatus

# Import all models to satisfy SQLAlchemy relationship resolution
from app.features.auth.models import User
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.features.assessments.models import Submission, Score
from app.features.proctoring.models import ProctoringSession, ProctoringEvent, ProctoringEvidence, RiskSnapshot
from app.features.interviews.models import InterviewFeedback
from app.features.audit.models import AuditLog
from app.features.analytics.models import AIGenerationLog

logger = logging.getLogger(__name__)

async def run_assessment_diagnostic():
    """Identify duplicate active assessments in the database."""
    print("\n🔍 Running Assessment Lifecycle Diagnostic...")
    async with async_session_factory() as sess:
        stmt = (
            select(
                Assessment.candidate_id, 
                Assessment.round, 
                func.count(Assessment.id).label('active_count')
            )
            .where(Assessment.status == AssessmentStatus.IN_PROGRESS)
            .group_by(Assessment.candidate_id, Assessment.round)
            .having(func.count(Assessment.id) > 1)
        )
        res = await sess.execute(stmt)
        duplicates = res.fetchall()
        
        if not duplicates:
            print("✅ No duplicate active assessments found. Lifecycle protection is intact.")
        else:
            print(f"⚠️  WARNING: Found {len(duplicates)} candidates with multiple active assessments!")
            for cand_id, round_val, count in duplicates:
                print(f"  - Candidate: {cand_id} | Round: {round_val} | Count: {count}")
    print("🏁 Diagnostic complete.\n")

if __name__ == "__main__":
    asyncio.run(run_assessment_diagnostic())
