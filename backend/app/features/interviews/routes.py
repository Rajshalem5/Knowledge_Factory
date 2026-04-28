"""Interview feedback routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.core.enums import Role
from app.features.interviews.models import InterviewFeedback

router = APIRouter()


@router.post("/candidates/{candidate_id}/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    candidate_id: UUID,
    feedback_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.INTERVIEWER, Role.ADMIN])),
):
    """Submit interviewer feedback for a candidate."""
    fb = InterviewFeedback(
        candidate_id=candidate_id,
        interviewer_id=current_user.id,
        technical=feedback_data.get("technicalScore", feedback_data.get("technical", 5)),
        problem_solving=feedback_data.get("problemSolving", 5),
        communication=feedback_data.get("communicationScore", feedback_data.get("communication", 5)),
        cultural_fit=feedback_data.get("culturalFit", 5),
        recommendation=feedback_data.get("recommendation", "HOLD"),
        comments=feedback_data.get("notes", feedback_data.get("comments")),
    )
    db.add(fb)
    await db.flush()
    return {"id": str(fb.id), "message": "Feedback submitted"}


@router.get("/candidates/{candidate_id}/feedback")
async def get_feedback(candidate_id: UUID, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))):
    stmt = select(InterviewFeedback).where(InterviewFeedback.candidate_id == candidate_id)
    res = await db.execute(stmt)
    fbs = res.scalars().all()
    return [
        {
            "id": fb.id,
            "technical": fb.technical,
            "problem_solving": fb.problem_solving,
            "communication": fb.communication,
            "cultural_fit": fb.cultural_fit,
            "recommendation": fb.recommendation if isinstance(fb.recommendation, str) else fb.recommendation.value,
            "comments": fb.comments,
            "submitted_at": fb.submitted_at.isoformat(),
            "interviewer_name": fb.interviewer.name if fb.interviewer else None,
        }
        for fb in fbs
    ]
