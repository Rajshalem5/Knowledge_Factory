"""
Candidate schemas: Lists, Details, Updates.
"""

from uuid import UUID
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal

from app.core.enums import CandidateStatus


class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    college: str
    branch: str
    cgpa: Decimal
    passed_out_year: int
    language_choice: str


class CandidateRead(CandidateBase):
    id: UUID
    status: CandidateStatus
    display_status: str = ""
    created_at: datetime
    cycle_id: UUID
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    govt_id_url: Optional[str] = None
    scores: list = []
    proctoring_flags: list = []
    interview_feedback: Optional[dict] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_compat(cls, candidate) -> "CandidateRead":
        """Build a CandidateRead from an ORM model, computing display_status and nested relations."""
        status_val = CandidateStatus(candidate.status) if isinstance(candidate.status, str) else candidate.status
        
        # Build scores
        scores = []
        if hasattr(candidate, 'scores') and candidate.scores:
            for s in candidate.scores:
                scores.append({
                    "round": s.round.value if hasattr(s.round, 'value') else str(s.round),
                    "score": float(s.weighted_total),
                    "maxScore": 100,
                    "completedAt": s.evaluated_at.isoformat() if s.evaluated_at else None,
                })
        
        # Build interview feedback
        interview_feedback = None
        if hasattr(candidate, 'interview_feedback') and candidate.interview_feedback:
            fb_list = candidate.interview_feedback if isinstance(candidate.interview_feedback, list) else [candidate.interview_feedback]
            if fb_list:
                fb = fb_list[0]
                interview_feedback = {
                    "technicalScore": fb.technical,
                    "communicationScore": fb.communication,
                    "recommendation": fb.recommendation.value.lower() if hasattr(fb.recommendation, 'value') else str(fb.recommendation).lower(),
                    "notes": fb.comments or "",
                    "interviewerId": fb.interviewer_id or "",
                    "interviewerName": fb.interviewer.name if hasattr(fb, 'interviewer') and fb.interviewer else "",
                    "completedAt": fb.submitted_at.isoformat() if fb.submitted_at else None,
                }
        
        return cls(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            college=candidate.college,
            branch=candidate.branch,
            cgpa=candidate.cgpa,
            passed_out_year=candidate.passed_out_year,
            language_choice=candidate.language_choice,
            phone=getattr(candidate, 'phone', None),
            resume_url=getattr(candidate, 'resume_url', None),
            govt_id_url=getattr(candidate, 'govt_id_url', None),
            status=status_val,
            display_status=status_val.display_status,
            created_at=candidate.created_at,
            cycle_id=candidate.cycle_id,
            scores=scores,
            interview_feedback=interview_feedback,
        )


class CandidateListResponse(BaseModel):
    data: list[CandidateRead]
    pagination: dict[str, Any]


class CandidateStatusUpdate(BaseModel):
    status: CandidateStatus


class BulkUploadPreview(BaseModel):
    batch_id: str
    total_records: int
    valid_records: int
    invalid_records: int
    preview: list[dict]
    errors: list[dict]
