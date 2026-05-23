from sqlalchemy import create_engine
from app.database import Base, engine
from app.config import settings
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

def init():
    # Use sync engine for Base.metadata.create_all
    sync_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    sync_engine = create_engine(sync_url)
    Base.metadata.create_all(bind=sync_engine)
    print("Tables created")

if __name__ == "__main__":
    init()
