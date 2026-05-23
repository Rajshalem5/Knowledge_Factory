"""Seed the database with realistic candidates for testing."""
import asyncio
import random
import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import select, delete

# Add current directory to path so app imports work
sys.path.insert(0, ".")

from app.database import async_session_factory, Base

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

from app.core.enums import CandidateStatus, EvaluationRecommendation, CycleStatus
from app.core.security import hash_password

CANDIDATE_NAMES = [
    "Alice Sharma", "Bob Patel", "Charlie Singh", "Divya Kumar", "Esha Gupta",
    "Farhan Qureshi", "Gauri Joshi", "Harish Reddy", "Ishita Verma", "Jatin Mehta",
    "Kavita Nair", "Lokesh Yadav", "Megha Rao", "Nitin Gadkari", "Ojaswi Mishra",
    "Priyanka Chopra", "Qasim Khan", "Rohan Das", "Sanya Mirza", "Tarun Khanna",
    "Urvashi Rautela", "Varun Dhawan", "Waseem Akram", "Xavier Rodrigues", "Yash Chopra",
    "Zoya Akhtar", "Amitabh Bachchan", "Bhuvan Bam", "Carry Minati", "Deepika Padukone",
    "Emraan Hashmi", "Farhan Akhtar", "Genelia D'Souza", "Hrithik Roshan", "Irrfan Khan",
    "Jacqueline Fernandez", "Kangana Ranaut", "Lata Mangeshkar", "Manoj Bajpayee", "Nawazuddin Siddiqui"
]

COLLEGES = ["IIT Bombay", "IIT Delhi", "NIT Trichy", "BITS Pilani", "DTU Delhi", "VIT Vellore", "SRM Chennai", "COEP Pune", "RVCE Bangalore", "PSG Tech"]
BRANCHES = ["CSE", "ECE", "IT", "EEE", "MECH", "CIVIL"]
LANGUAGES = ["python", "java", "cpp", "javascript"]
SKILLS_LIST = ["React", "Node.js", "Python", "SQL", "Machine Learning", "Cloud Computing", "C++", "Java", "Docker", "Kubernetes"]

STATUS_MAPPING = {
    "APPLIED": CandidateStatus.APPLIED,
    "ELIGIBLE": CandidateStatus.ROUND1_PASSED,
    "ROUND1_PASSED": CandidateStatus.ROUND2_PASSED,
    "ROUND2_PASSED": CandidateStatus.ROUND3_PASSED,
    "ROUND3_PASSED": CandidateStatus.INTERVIEW_SCHEDULED,
    "INTERVIEWED": CandidateStatus.INTERVIEW_COMPLETED,
    "SELECTED": CandidateStatus.SELECTED,
    "REJECTED": CandidateStatus.FINAL_REJECTED
}

async def seed():
    async with async_session_factory() as session:
        async with session.begin():
            # ── Ensure Active Hiring Cycle ────────────────────────
            stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE")
            cycle = (await session.execute(stmt)).scalar_one_or_none()
            if not cycle:
                cycle = HiringCycle(
                    name="Standard Recruitment 2026",
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 12, 31),
                    status=CycleStatus.ACTIVE,
                    eligibility_config={"min_cgpa": 6.0, "allowed_branches": ["CSE", "ECE", "IT", "EEE", "MECH", "CIVIL"]},
                )
                session.add(cycle)
                await session.flush()
                print(f"Created hiring cycle: {cycle.id}")
            else:
                print(f"Using existing cycle: {cycle.id}")

            # ── Clear Existing Candidates ──────────────────────────
            print("Clearing existing candidates...")
            await session.execute(delete(Candidate))
            
            # ── Seed Candidates ────────────────────────────────────
            candidates_inserted = 0
            
            for status_label, status_enum in STATUS_MAPPING.items():
                print(f"Seeding 5 candidates for status: {status_label}")
                for i in range(5):
                    name_idx = candidates_inserted % len(CANDIDATE_NAMES)
                    name = CANDIDATE_NAMES[name_idx]
                    if candidates_inserted >= len(CANDIDATE_NAMES):
                        name = f"{name} {i+1}"
                    
                    email = f"{name.lower().replace(' ', '.')}@example.com"
                    
                    # Randomized data
                    college = random.choice(COLLEGES)
                    branch = random.choice(BRANCHES)
                    cgpa = Decimal(str(round(random.uniform(6.5, 9.8), 2)))
                    grad_year = random.choice([2024, 2025, 2026])
                    lang = random.choice(LANGUAGES)
                    skills = ", ".join(random.sample(SKILLS_LIST, k=random.randint(2, 5)))
                    
                    # Score generation based on status
                    screening = Decimal("0.0")
                    mcq = Decimal("0.0")
                    coding = Decimal("0.0")
                    risk = Decimal("0.0")
                    composite = Decimal("0.0")
                    adjusted = Decimal("0.0")
                    recommendation = None
                    
                    if status_label != "APPLIED":
                        screening = Decimal(str(round(random.uniform(70, 95), 2)))
                    
                    if status_label in ["ROUND1_PASSED", "ROUND2_PASSED", "ROUND3_PASSED", "INTERVIEWED", "SELECTED"]:
                        mcq = Decimal(str(round(random.uniform(70, 95), 2)))
                    
                    if status_label in ["ROUND2_PASSED", "ROUND3_PASSED", "INTERVIEWED", "SELECTED"]:
                        coding = Decimal(str(round(random.uniform(70, 95), 2)))
                    
                    if status_label == "REJECTED":
                        # Either low scores or high risk
                        if random.choice([True, False]):
                            screening = Decimal(str(round(random.uniform(10, 50), 2)))
                            mcq = Decimal(str(round(random.uniform(10, 50), 2)))
                        else:
                            screening = Decimal(str(round(random.uniform(70, 90), 2)))
                            risk = Decimal(str(round(random.uniform(60, 100), 2)))
                    
                    if status_label == "SELECTED":
                        screening = Decimal(str(round(random.uniform(85, 98), 2)))
                        mcq = Decimal(str(round(random.uniform(85, 98), 2)))
                        coding = Decimal(str(round(random.uniform(80, 98), 2)))
                        risk = Decimal(str(round(random.uniform(0, 5), 2)))
                    
                    # Calculate composite and adjusted
                    if screening > 0:
                        composite = (screening * Decimal("0.2")) + (mcq * Decimal("0.3")) + (coding * Decimal("0.5"))
                        adjusted = composite - risk
                        
                        if adjusted >= 80:
                            recommendation = EvaluationRecommendation.STRONGLY_RECOMMENDED
                        elif adjusted >= 70:
                            recommendation = EvaluationRecommendation.RECOMMENDED
                        elif adjusted >= 50:
                            recommendation = EvaluationRecommendation.BORDERLINE
                        else:
                            recommendation = EvaluationRecommendation.NOT_RECOMMENDED

                    candidate = Candidate(
                        cycle_id=cycle.id,
                        email=email,
                        name=name,
                        college=college,
                        branch=branch,
                        cgpa=cgpa,
                        passed_out_year=grad_year,
                        language_choice=lang,
                        skills=skills,
                        status=status_enum,
                        password_hash=hash_password("Welcome@123"),
                        screening_score=screening,
                        mcq_score=mcq,
                        coding_score=coding,
                        risk_penalty=risk,
                        composite_score=composite,
                        adjusted_final_score=adjusted,
                        recommendation=recommendation,
                        resume_url=f"/uploads/resumes/{email.replace('@', '_')}_resume.pdf",
                        email_verified=True
                    )
                    session.add(candidate)
                    candidates_inserted += 1

            print(f"Successfully inserted {candidates_inserted} candidates.")

    print("\nSeed complete!")

if __name__ == "__main__":
    asyncio.run(seed())
