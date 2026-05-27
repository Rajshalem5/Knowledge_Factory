"""Selection routes: final hiring decisions."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.core.enums import Role, CandidateStatus
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional
from app.features.selection.service import EvaluationService
from app.features.candidates.schemas import CandidateRead

router = APIRouter()

class DecisionRequest(BaseModel):
    status: CandidateStatus
    reason: Optional[str] = None

@router.get("/ranking/{cycle_id}", response_model=list[CandidateRead])
async def get_ranking(cycle_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))):
    """Get ranked candidates for a hiring cycle."""
    service = EvaluationService(db)
    candidates = await service.get_ranked_candidates(cycle_id)
    return [CandidateRead.from_orm_compat(c) for c in candidates]

@router.post("/candidates/{candidate_id}/decision")
async def make_decision(
    candidate_id: str, 
    req: DecisionRequest,
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))
):
    """Make a final hiring decision (Select, Reject, Waitlist) with reason and audit trail."""
    stmt = select(Candidate).where(Candidate.id == str(candidate_id))
    res = await db.execute(stmt)
    c = res.scalar_one_or_none()

    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Update status and audit fields
    c.status = req.status
    c.decision_reason = req.reason
    c.decision_by = str(current_user.id)
    c.decision_timestamp = datetime.now(timezone.utc)
    
    await db.flush()
    return {
        "id": str(c.id), 
        "status": c.status, 
        "decision_by": c.decision_by, 
        "decision_timestamp": c.decision_timestamp
    }

@router.post("/candidates/{candidate_id}/select")
async def select_candidate(candidate_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))):
    """Select a candidate (convenience wrapper)."""
    return await make_decision(candidate_id, DecisionRequest(status=CandidateStatus.SELECTED), db, current_user)

@router.post("/candidates/{candidate_id}/reject")
async def reject_candidate(candidate_id: str, reason: str | None = None, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))):
    """Reject a candidate (convenience wrapper)."""
    return await make_decision(candidate_id, DecisionRequest(status=CandidateStatus.FINAL_REJECTED, reason=reason), db, current_user)
