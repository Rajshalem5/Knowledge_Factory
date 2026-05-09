"""Assessment service: start, submit, evaluate."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AssessmentRound, AssessmentStatus, CandidateStatus, SubmissionSection
from app.features.assessments.models import Assessment, Submission, Score
from app.features.assessments.schemas import AssessmentStart, SubmissionCreate
from app.features.candidates.models import Candidate
from app.features.proctoring.models import ProctoringRecord


class AssessmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_assessment(self, candidate_id: UUID, req: AssessmentStart) -> Assessment:
        # Validate candidate exists and has correct pipeline status
        c_stmt = select(Candidate).where(Candidate.id == candidate_id)
        c_res = await self.db.execute(c_stmt)
        candidate = c_res.scalar_one_or_none()
        if not candidate:
            raise ValueError("Candidate not found")

        # Round-to-status mapping: required current status → target status on start
        round_status_map = {
            AssessmentRound.ROUND_2: (CandidateStatus.ROUND1_PASSED, CandidateStatus.ROUND2_IN_PROGRESS),
            AssessmentRound.ROUND_3: (CandidateStatus.ROUND2_PASSED, CandidateStatus.ROUND3_IN_PROGRESS),
        }
        status_mapping = round_status_map.get(req.round)
        if status_mapping:
            required_status, next_status = status_mapping
            if candidate.status != required_status:
                raise ValueError(
                    f"Candidate must be in {required_status.value} to start {req.round.value} assessment"
                )
            candidate.status = next_status

        # Check if candidate already has an active/in-progress assessment for this round
        stmt = (
            select(Assessment)
            .where(
                Assessment.candidate_id == candidate_id,
                Assessment.round == req.round,
                Assessment.status.in_([AssessmentStatus.IN_PROGRESS]),
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # Create new assessment
        assessment = Assessment(
            candidate_id=candidate_id,
            round=req.round,
            questions_json=self._generate_sample_questions(req.round),
            link_token=uuid.uuid4().hex,
            link_expiry=datetime.now(timezone.utc) + timedelta(days=5),
            started_at=datetime.now(timezone.utc),
            status=AssessmentStatus.IN_PROGRESS,
        )
        self.db.add(assessment)

        # Create proctoring record
        proctoring = ProctoringRecord(
            assessment_id=assessment.id,
            candidate_id=candidate_id,
            retention_expiry=datetime.now(timezone.utc).date() + timedelta(days=20),
        )
        self.db.add(proctoring)

        await self.db.flush()
        return assessment

    async def submit_section(self, candidate_id: UUID, data: SubmissionCreate) -> dict[str, Any]:
        """Submit a section. Returns passed/failed test case counts."""
        # Verify the candidate owns this assessment
        stmt = select(Assessment).where(Assessment.id == data.assessment_id)
        res = await self.db.execute(stmt)
        assessment = res.scalar_one_or_none()

        if not assessment or assessment.candidate_id != candidate_id:
            raise ValueError("Assessment not found or access denied")

        # Create submission
        section = SubmissionSection.CODING if data.section in ("CODING", "coding") else SubmissionSection.MCQ
        submission = Submission(
            assessment_id=data.assessment_id,
            section=section,
            payload_json={"code" if data.section == "CODING" else "answers": data.content},
        )
        self.db.add(submission)

        # Mock evaluation — in prod this goes to Judge0 + AI pipeline
        passed = len(data.content.get("testCases", []))
        failed = 0

        await self.db.flush()
        return {"submission_id": submission.id, "passed": passed, "failed": failed}

    async def get_assessment(self, candidate_id: UUID) -> list[Assessment]:
        stmt = (
            select(Assessment)
            .where(Assessment.candidate_id == candidate_id)
            .order_by(Assessment.started_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    def _generate_sample_questions(round_type: AssessmentRound) -> dict:
        """Generate sample questions for development. Replace with AI engine in production."""
        if round_type == AssessmentRound.ROUND_2:
            return {
                "problems": [
                    {
                        "id": "r2_p1",
                        "title": "Two Sum",
                        "description": "Given an array of integers nums and an integer target, return indices of the two numbers...",
                        "difficulty": "easy",
                        "starter_code": "def two_sum(nums, target):\n    # write your code here\n    pass",
                        "test_cases": [
                            {"input": "[2,7,11,15], 9", "expectedOutput": "[0,1]"},
                            {"input": "[3,2,4], 6", "expectedOutput": "[1,2]"},
                        ],
                    }
                ]
            }
        return {"use_case": "Build a REST API endpoint for user registration with input validation."}
