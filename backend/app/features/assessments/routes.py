"""
Assessment routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.features.assessments.schemas import AssessmentStart, AssessmentRead, SubmissionCreate
from app.features.assessments.service import AssessmentService
from app.core.enums import Role

router = APIRouter()


@router.post("/start", response_model=AssessmentRead)
async def start_assessment(
    start_data: AssessmentStart,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user) # Candidate
):
    """
    Start an assessment round (Round 2 or 3).
    """
    service = AssessmentService(db)
    # Check if user is a candidate
    # (Simplified for MVP, ideally use a specific dependency)
    candidate_id = current_user.id
    return await service.start_assessment(candidate_id, start_data)


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_section(
    submission_data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit a section (MCQ, Coding, or UseCase).
    """
    service = AssessmentService(db)
    return await service.submit_section(current_user.id, submission_data)
