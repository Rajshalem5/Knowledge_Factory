import asyncio
import os
import sys

# Add the directory containing 'app' to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Ensure we use the correct local database path
db_path = os.path.join(backend_dir, "knowledge_factory.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"

from sqlalchemy import select
from app.database import async_session_factory
from app.features.candidates.models import Candidate

# Import other models to satisfy relationship initialization
from app.features.hiring_cycles.models import HiringCycle
from app.features.assessments.models import Assessment, Score, Submission
from app.features.proctoring.models import (
    ProctoringSession,
    ProctoringEvent,
    ProctoringEvidence,
    RiskSnapshot,
)
from app.features.interviews.models import InterviewFeedback
from app.features.auth.models import User


async def delete_candidate(email: str):
    async with async_session_factory() as session:
        stmt = select(Candidate).where(Candidate.email == email)
        result = await session.execute(stmt)
        candidate = result.scalar_one_or_none()

        if not candidate:
            print(f"❌ Candidate with email '{email}' not found.")
            return

        print("\nCandidate Found:")
        print(f"Name  : {candidate.name}")
        print(f"Email : {candidate.email}")
        print(f"ID    : {candidate.id}")

        confirm = input("\nAre you sure you want to delete this candidate? (y/n): ")

        if confirm.lower() != "y":
            print("❌ Deletion cancelled.")
            return

        await session.delete(candidate)
        await session.commit()

        print("✅ Candidate deleted successfully.")


if __name__ == "__main__":
    email = input("Enter candidate email to delete: ").strip()

    if not email:
        print("❌ Email cannot be empty.")
        sys.exit(1)

    asyncio.run(delete_candidate(email))