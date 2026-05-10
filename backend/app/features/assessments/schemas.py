"""
Assessment schemas: Questions, Submissions, Scores.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel

from app.core.enums import AssessmentRound, AssessmentStatus, SubmissionSection


class AssessmentStart(BaseModel):
    round: AssessmentRound


class AssessmentRead(BaseModel):
    id: str
    candidate_id: str
    round: AssessmentRound
    status: AssessmentStatus
    questions_json: dict
    link_token: str
    link_expiry: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    time_limit: int = 60

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    assessment_id: str
    section: SubmissionSection
    content: dict # MCQ answers or Code string
    time_spent_seconds: int

