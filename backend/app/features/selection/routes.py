"""Selection routes: final hiring decisions."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.core.enums import Role, CandidateStatus
from app.features.candidates.models import Candidate

router = APIRouter()


@router.post("/candidates/{candidate_id}/select")
async def select_candidate(candidate_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))):
    """Select a candidate — moves them to SELECTED status."""
    stmt = select(Candidate).where(Candidate.id == str(candidate_id))
    res = await db.execute(stmt)
    c = res.scalar_one_or_none()

    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")

    allowed = {CandidateStatus.INTERVIEW_COMPLETED, CandidateStatus.ROUND3_PASSED}
    current = CandidateStatus(c.status) if isinstance(c.status, str) else c.status
    if current not in allowed:
        raise HTTPException(status_code=422, detail=f"Cannot select from status {current.value}")

    c.status = CandidateStatus.SELECTED
    await db.flush()
    return {"id": str(c.id), "status": "SELECTED"}


@router.post("/candidates/bulk-select", status_code=status.HTTP_200_OK)
async def bulk_select(bodies: list[dict], db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))):
    """Bulk select candidates."""
    results = []
    for body in bodies:
        cid = body["candidate_id"]
        stmt = select(Candidate).where(Candidate.id == cid)
        res = await db.execute(stmt)
        c = res.scalar_one_or_none()
        if c and c.status in (CandidateStatus.INTERVIEW_COMPLETED, CandidateStatus.ROUND3_PASSED):
            c.status = CandidateStatus.SELECTED
            results.append({"id": str(c.id), "status": "selected"})
        else:
            results.append({"id": str(cid), "error": "Cannot select"})
    await db.flush()
    return {"results": results}


@router.post("/candidates/{candidate_id}/reject", status_code=status.HTTP_200_OK)
async def reject_candidate(candidate_id: str, reason: str | None = None, db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))):
    """Reject a candidate."""
    stmt = select(Candidate).where(Candidate.id == str(candidate_id))
    res = await db.execute(stmt)
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    c.status = CandidateStatus.FINAL_REJECTED
    await db.flush()
    return {"id": str(c.id), "status": "REJECTED"}
