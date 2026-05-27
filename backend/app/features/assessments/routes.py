"""Assessment routes — restricted to CANDIDATE role (except HR-triggered)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CANDIDATE_ONLY, get_current_user, require_role
from app.features.assessments.schemas import AssessmentStart, AssessmentRead, SubmissionCreate, AssessmentResult, AssessmentAdminRead
from app.features.assessments.service import AssessmentService
from app.core.enums import Role, AssessmentStatus, AssessmentRound

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{assessment_id}/admin", response_model=AssessmentAdminRead)
async def get_assessment_admin(assessment_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Get full assessment details including submissions for admin review."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.features.assessments.models import Assessment
    
    stmt = select(Assessment).options(selectinload(Assessment.submissions)).where(Assessment.id == assessment_id)
    res = await db.execute(stmt)
    assessment = res.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.post("/start", response_model=AssessmentRead)
async def start_assessment(start_data: AssessmentStart, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    logger.info(
        "POST /api/assessment/start | candidate_id=%s | round=%s | payload=%s",
        current_user.id, start_data.round, start_data.model_dump(),
    )
    service = AssessmentService(db)
    try:
        result = await service.start_assessment(current_user.id, start_data)
        logger.info(
            "POST /api/assessment/start success | assessment_id=%s | round=%s | status=%s",
            result.id, result.round, result.status,
        )
        return result
    except ValueError as e:
        logger.warning(
            "POST /api/assessment/start failed 400 | candidate_id=%s | round=%s | detail=%s",
            current_user.id, start_data.round, str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/active", response_model=list[AssessmentRead])
async def get_active_assessments(db: AsyncSession = Depends(get_db), current_user = Depends(CANDIDATE_ONLY)):
    """Get all active/in-progress assessments for the candidate."""
    service = AssessmentService(db)
    assessments = await service.get_assessment(current_user.id)
    logger.info("GET /api/assessment/active | candidate_id=%s | count=%d", current_user.id, len(assessments))
    return assessments


@router.post("/{assessment_id}/complete", response_model=AssessmentRead)
async def complete_assessment(assessment_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(CANDIDATE_ONLY)):
    """Mark an assessment as completed and advance the candidate to the next pipeline stage."""
    service = AssessmentService(db)
    try:
        assessment = await service.complete_assessment(current_user.id, assessment_id)
        # Convert to Pydantic and then to dict to be absolutely safe
        return AssessmentRead.model_validate(assessment).model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Complete assessment error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{assessment_id}/result", response_model=AssessmentResult)
async def get_assessment_result(assessment_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Fetch the result summary for a completed assessment."""
    service = AssessmentService(db)
    try:
        return await service.get_assessment_result(current_user.id, assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


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
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN])),
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
