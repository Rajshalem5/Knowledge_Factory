import asyncio
from app.database import Base, engine
# Import all models to ensure they are registered with Base.metadata
from app.features.auth.models import User
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.features.assessments.models import Assessment, Submission, Score
from app.features.proctoring.models import ProctoringSession, ProctoringEvent, ProctoringEvidence, RiskSnapshot
from app.features.interviews.models import InterviewFeedback
from app.features.audit.models import AuditLog
from app.features.analytics.models import AIGenerationLog
from app.features.notifications.models import EmailLog

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created")

if __name__ == "__main__":
    asyncio.run(init())
