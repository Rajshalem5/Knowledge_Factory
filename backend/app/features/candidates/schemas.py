"""
Candidate schemas: Lists, Details, Updates.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from app.core.enums import CandidateStatus, EvaluationRecommendation


class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    college: str
    branch: str
    cgpa: float
    passed_out_year: int
    language_choice: str
    degree: Optional[str] = None
    skills: Optional[str] = None


class CandidateRead(CandidateBase):
    id: str
    status: CandidateStatus
    display_status: str = ""
    email_verified: bool = False
    created_at: datetime
    updated_at: datetime
    cycle_id: str
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    govt_id_url: Optional[str] = None
    custom_fields: dict = {}
    scores: list = []
    proctoring_flags: list = []
    interview_feedback: Optional[dict] = None

    # Evaluation results
    screening_score: float = 0.0
    mcq_score: float = 0.0
    coding_score: float = 0.0
    risk_penalty: float = 0.0
    composite_score: float = 0.0
    adjusted_final_score: float = 0.0
    recommendation: Optional[EvaluationRecommendation] = None

    # Decision details
    decision_reason: Optional[str] = None
    decision_by: Optional[str] = None
    decision_timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

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
                    "score": float(s.weighted_total) if s.weighted_total is not None else 0.0,
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

        # Build proctoring flags from violations_json
        proctoring_flags = []
        if hasattr(candidate, 'proctoring_records') and candidate.proctoring_records:
            for record in candidate.proctoring_records:
                violations = record.violations_json or []
                for i, v in enumerate(violations):
                    proctoring_flags.append({
                        "id": f"{record.id}_{i}",
                        "type": v.get("type", "unknown"),
                        "timestamp": v.get("timestamp", ""),
                        "details": str(v.get("evidence", {})),
                    })
        
        return cls(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            college=candidate.college,
            branch=candidate.branch,
            cgpa=candidate.cgpa,
            passed_out_year=candidate.passed_out_year,
            language_choice=candidate.language_choice,
            degree=getattr(candidate, 'degree', None),
            skills=getattr(candidate, 'skills', None),
            email_verified=getattr(candidate, 'email_verified', False),
            phone=getattr(candidate, 'phone', None),
            resume_url=getattr(candidate, 'resume_url', None),
            govt_id_url=getattr(candidate, 'govt_id_url', None),
            custom_fields=getattr(candidate, 'custom_fields', {}),
            status=status_val,
            display_status=status_val.display_status,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
            cycle_id=candidate.cycle_id,
            scores=scores,
            interview_feedback=interview_feedback,
            proctoring_flags=proctoring_flags,
            screening_score=float(getattr(candidate, 'screening_score', 0.0)),
            mcq_score=float(getattr(candidate, 'mcq_score', 0.0)),
            coding_score=float(getattr(candidate, 'coding_score', 0.0)),
            risk_penalty=float(getattr(candidate, 'risk_penalty', 0.0)),
            composite_score=float(getattr(candidate, 'composite_score', 0.0)),
            adjusted_final_score=float(getattr(candidate, 'adjusted_final_score', 0.0)),
            recommendation=getattr(candidate, 'recommendation', None),
            decision_reason=getattr(candidate, 'decision_reason', None),
            decision_by=getattr(candidate, 'decision_by', None),
            decision_timestamp=getattr(candidate, 'decision_timestamp', None),
        )


class CandidateListResponse(BaseModel):
    data: list[CandidateRead]
    pagination: dict[str, Any]


class CandidateStatusUpdate(BaseModel):
    status: CandidateStatus

    @field_validator("status", mode="before")
    @classmethod
    def coerce_status(cls, v: object) -> CandidateStatus:
        """Accept both canonical enum values (SELECTED, ROUND1_PASSED) and display statuses (selected, round1)."""
        if isinstance(v, CandidateStatus):
            return v
        raw = str(v)
        # Try canonical enum value first (case-insensitive)
        try:
            return CandidateStatus(raw.upper())
        except ValueError:
            pass
        # Try display status mapping
        mapped = CandidateStatus.from_display_status(raw)
        if mapped is not None:
            return mapped
        raise ValueError(f"Invalid status: {raw}")


class BulkUploadPreview(BaseModel):
    batch_id: str
    total_records: int
    valid_records: int
    invalid_records: int
    preview: list[dict]
    errors: list[dict]

class DuplicateCandidate(BaseModel):
    email: str
    reason: str

class BulkUploadResponse(BaseModel):
    batch_id: str
    total_records: int
    created: int
    updated: int
    skipped: int
    errors: list[dict]
    duplicates: list[DuplicateCandidate]
