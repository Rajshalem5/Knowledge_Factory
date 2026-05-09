"""Screening routes: Round 1 eligibility filtering."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.features.candidates.models import Candidate
from app.core.enums import Role, CandidateStatus

router = APIRouter()


@router.post("/run")
async def run_screening(
    branch: str | None = Query(None, description="Optional filter: only screen candidates from this branch"),
    college: str | None = Query(None, description="Optional filter: only screen candidates from this college"),
    passed_out_year: int | None = Query(None, description="Optional filter: only screen candidates from this passed-out year"),
    language_choice: str | None = Query(None, description="Optional filter: only screen candidates with this language choice"),
    min_cgpa_override: float | None = Query(None, ge=0.0, le=10.0, description="Override the cycle's min_cgpa threshold"),
    db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN]))):
    """
    Auto-screen candidates based on hiring cycle config.
    Candidates meeting CGPA/branch criteria transition from APPLIED to ROUND1_PASSED.
    Others go to ROUND1_REJECTED.

    Supports optional extra filtering (branch, college, passed_out_year, language_choice) and
    min_cgpa_override to run targeted screening rounds.
    """
    # Get the active cycle
    from app.features.hiring_cycles.models import HiringCycle
    stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE")
    res = await db.execute(stmt)
    cycle = res.scalar_one_or_none()

    if not cycle:
        raise HTTPException(status_code=400, detail="No active hiring cycle found")

    cfg = cycle.eligibility_config or {}
    min_cgpa = float(min_cgpa_override) if min_cgpa_override is not None else float(cfg.get("min_cgpa", 6.0))
    allowed_branches = cfg.get("allowed_branches", [])

    q = select(Candidate).where(
        Candidate.status == CandidateStatus.APPLIED,
    )

    # Extra optional filters
    if branch:
        q = q.where(Candidate.branch.ilike(f"%{branch}%"))
    if college:
        q = q.where(Candidate.college.ilike(f"%{college}%"))
    if passed_out_year:
        q = q.where(Candidate.passed_out_year == passed_out_year)
    if language_choice:
        q = q.where(Candidate.language_choice.ilike(f"%{language_choice}%"))

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
    return {"screened": len(candidates), "passed": passed, "rejected": rejected, "min_cgpa": min_cgpa, "allowed_branches": allowed_branches}


@router.get("/pipeline-stats")
async def pipeline_stats(
    branch: str | None = Query(None, description="Optional filter by branch"),
    college: str | None = Query(None, description="Optional filter by college"),
    passed_out_year: int | None = Query(None, description="Optional filter by passed-out year"),
    language_choice: str | None = Query(None, description="Optional filter by language choice"),
    cgpa_min: float | None = Query(None, ge=0.0, le=10.0, description="Optional min CGPA filter"),
    cgpa_max: float | None = Query(None, ge=0.0, le=10.0, description="Optional max CGPA filter"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN])),
):
    """Get aggregated candidate counts per pipeline stage with optional extra filters."""
    base = select(Candidate.status, func.count(Candidate.id).label("count"))
    if branch:
        base = base.where(Candidate.branch.ilike(f"%{branch}%"))
    if college:
        base = base.where(Candidate.college.ilike(f"%{college}%"))
    if passed_out_year:
        base = base.where(Candidate.passed_out_year == passed_out_year)
    if language_choice:
        base = base.where(Candidate.language_choice.ilike(f"%{language_choice}%"))
    if cgpa_min is not None:
        base = base.where(Candidate.cgpa >= cgpa_min)
    if cgpa_max is not None:
        base = base.where(Candidate.cgpa <= cgpa_max)
    base = base.group_by(Candidate.status)

    res = await db.execute(base)
    rows = res.all()
    stats = {row.status: row.count for row in rows}

    # Ensure all statuses appear even when 0
    for s in CandidateStatus:
        stats.setdefault(s.value, 0)

    return {"stats": dict(sorted(stats.items()))}
