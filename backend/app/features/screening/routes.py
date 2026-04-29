"""Screening routes: Round 1 eligibility filtering."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.features.candidates.models import Candidate
from app.core.enums import Role, CandidateStatus

router = APIRouter()


@router.post("/run")
async def run_screening(db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN]))):
    """
    Auto-screen candidates based on hiring cycle config.
    Candidates meeting CGPA/branch criteria transition from APPLIED to ROUND1_PASSED.
    Others go to ROUND1_REJECTED.
    """
    # Get the active cycle
    from app.features.hiring_cycles.models import HiringCycle
    stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE")
    res = await db.execute(stmt)
    cycle = res.scalar_one_or_none()

    if not cycle:
        raise HTTPException(status_code=400, detail="No active hiring cycle found")

    cfg = cycle.eligibility_config or {}
    min_cgpa = float(cfg.get("min_cgpa", 6.0))
    allowed_branches = cfg.get("allowed_branches", [])

    q = select(Candidate).where(
        Candidate.status == CandidateStatus.APPLIED,
    )
    res = await db.execute(q)
    candidates = res.scalars().all()

    passed = 0
    rejected = 0

    for c in candidates:
        cgpa_val = float(c.cgpa)
        branch_ok = not allowed_branches or c.branch.lower() in [b.lower() for b in allowed_branches]

        if cgpa_val >= min_cgpa and branch_ok:
            c.status = CandidateStatus.ROUND1_PASSED
            passed += 1
        else:
            c.status = CandidateStatus.ROUND1_REJECTED
            rejected += 1

    await db.flush()
    return {"screened": len(candidates), "passed": passed, "rejected": rejected}
