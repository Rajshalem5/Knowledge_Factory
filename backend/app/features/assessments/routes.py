"""Assessment routes — restricted to CANDIDATE role (except HR-triggered)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CANDIDATE_ONLY, require_role
from app.features.assessments.schemas import AssessmentStart, AssessmentRead, SubmissionCreate
from app.features.assessments.service import AssessmentService
from app.core.enums import Role, AssessmentStatus, AssessmentRound

router = APIRouter()


@router.post("/start", response_model=AssessmentRead)
async def start_assessment(start_data: AssessmentStart, db: AsyncSession = Depends(get_db), current_user = Depends(CANDIDATE_ONLY)):
    service = AssessmentService(db)
    try:
        return await service.start_assessment(current_user.id, start_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/active", response_model=list[AssessmentRead])
async def get_active_assessments(db: AsyncSession = Depends(get_db), current_user = Depends(CANDIDATE_ONLY)):
    """Get all active/in-progress assessments for the candidate."""
    service = AssessmentService(db)
    return await service.get_assessment(current_user.id)


@router.post("/{assessment_id}/complete", response_model=AssessmentRead)
async def complete_assessment(assessment_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(CANDIDATE_ONLY)):
    """Mark an assessment as completed and advance the candidate to the next pipeline stage."""
    service = AssessmentService(db)
    try:
        return await service.complete_assessment(current_user.id, assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{assessment_id}", response_model=AssessmentRead)
async def get_assessment_by_id(assessment_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(CANDIDATE_ONLY)):
    """Get a single assessment by its ID."""
    from sqlalchemy import select
    from app.features.assessments.models import Assessment
    stmt = select(Assessment).where(Assessment.id == assessment_id)
    res = await db.execute(stmt)
    assessment = res.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.post("/submit-section", response_model=dict)
async def submit_section(submission_data: SubmissionCreate, db: AsyncSession = Depends(get_db), current_user = Depends(CANDIDATE_ONLY)):
    service = AssessmentService(db)
    try:
        result = await service.submit_section(current_user.id, submission_data)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower() or "access denied" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    return result


@router.post("/hr-start/{candidate_id}", status_code=status.HTTP_201_CREATED)
async def hr_start_assessment(
    candidate_id: str,
    start_data: AssessmentStart,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    """HR/admin-triggered: start an assessment for a candidate.

    This bypasses the candidate portal flow so HR can manually assign
    an assessment to a candidate who should move to the next round.
    """
    service = AssessmentService(db)
    try:
        assessment = await service.start_assessment(candidate_id, start_data)
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
