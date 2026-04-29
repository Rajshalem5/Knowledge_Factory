"""Assessment routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.features.assessments.schemas import AssessmentStart, AssessmentRead, SubmissionCreate
from app.features.assessments.service import AssessmentService
from app.core.enums import Role, AssessmentStatus

router = APIRouter()


@router.post("/start", response_model=AssessmentRead)
async def start_assessment(start_data: AssessmentStart, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    service = AssessmentService(db)
    return await service.start_assessment(current_user.id, start_data)


@router.get("/active", response_model=list[AssessmentRead])
async def get_active_assessments(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Get all active/in-progress assessments for the candidate."""
    service = AssessmentService(db)
    return await service.get_assessment(current_user.id)


@router.post("/submit-section", response_model=dict)
async def submit_section(submission_data: SubmissionCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    service = AssessmentService(db)
    try:
        result = await service.submit_section(current_user.id, submission_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result
