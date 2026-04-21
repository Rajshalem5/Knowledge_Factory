"""
Assessment business logic.
"""

import secrets
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.assessments.models import Assessment, Submission
from app.features.assessments.schemas import AssessmentStart, SubmissionCreate
from app.core.enums import AssessmentStatus, AssessmentRound


class AssessmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_assessment(self, candidate_id: UUID, start_data: AssessmentStart) -> Assessment:
        """
        Initialize an assessment round. 
        """
        # 1. Check if already exists
        stmt = select(Assessment).where(
            Assessment.candidate_id == candidate_id,
            Assessment.round == start_data.round
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing

        # 2. Create new assessment
        new_assessment = Assessment(
            candidate_id=candidate_id,
            round=start_data.round,
            status=AssessmentStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
            link_token=secrets.token_urlsafe(32),
            link_expiry=datetime.now(timezone.utc) + timedelta(days=5),
            questions_json={
                "questions": [
                    {"id": 1, "text": "Mock Question?", "options": ["A", "B"], "answer_idx": 0}
                ]
            }
        )
        self.db.add(new_assessment)
        await self.db.flush()
        return new_assessment

    async def submit_section(self, candidate_id: UUID, submission_data: SubmissionCreate) -> Submission:
        """
        Persist a candidate's submission.
        """
        new_submission = Submission(
            assessment_id=submission_data.assessment_id,
            section=submission_data.section,
            payload_json=submission_data.content,
            submitted_at=datetime.now(timezone.utc)
        )
        self.db.add(new_submission)
        await self.db.flush()
        
        # Mark assessment as completed (Simplified)
        await self.db.execute(
            update(Assessment).where(Assessment.id == submission_data.assessment_id)
            .values(status=AssessmentStatus.COMPLETED, ended_at=datetime.now(timezone.utc))
        )
        
        return new_submission
