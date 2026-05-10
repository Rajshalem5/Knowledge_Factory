"""Screening routes: Round 1 eligibility filtering."""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.features.candidates.models import Candidate
from app.core.enums import Role, CandidateStatus

router = APIRouter()


def _apply_extra_filters(q, branch, college, passed_out_year, language_choice, search,
                          name=None,
                          cgpa_min=None, cgpa_max=None,
                          has_resume=None, has_govt_id=None,
                          created_after=None, created_before=None,
                          passed_out_year_min=None, passed_out_year_max=None,
                          email_verified=None, phone=None, email=None):
    """Apply common extra filters to a Candidate query."""
    if name:
        q = q.where(Candidate.name.ilike(f"%{name}%"))
    if branch:
        q = q.where(Candidate.branch.ilike(f"%{branch}%"))
    if college:
        q = q.where(Candidate.college.ilike(f"%{college}%"))
    if passed_out_year:
        q = q.where(Candidate.passed_out_year == passed_out_year)
    if language_choice:
        q = q.where(Candidate.language_choice.ilike(f"%{language_choice}%"))
    if search:
        q = q.where(
            or_(
                Candidate.name.ilike(f"%{search}%"),
                Candidate.email.ilike(f"%{search}%"),
                Candidate.college.ilike(f"%{search}%"),
            )
        )
    if phone:
        q = q.where(Candidate.phone.ilike(f"%{phone}%"))
    if email:
        q = q.where(Candidate.email == email)
    if cgpa_min is not None:
        q = q.where(Candidate.cgpa >= cgpa_min)
    if cgpa_max is not None:
        q = q.where(Candidate.cgpa <= cgpa_max)
    if has_resume is not None:
        if has_resume:
            q = q.where(Candidate.resume_url.isnot(None))
        else:
            q = q.where(Candidate.resume_url.is_(None))
    if has_govt_id is not None:
        if has_govt_id:
            q = q.where(Candidate.govt_id_url.isnot(None))
        else:
            q = q.where(Candidate.govt_id_url.is_(None))
    if created_after:
        dt = datetime.combine(created_after, datetime.min.time())
        q = q.where(Candidate.created_at >= dt)
    if created_before:
        dt = datetime.combine(created_before, datetime.max.time())
        q = q.where(Candidate.created_at <= dt)
    if passed_out_year_min is not None:
        q = q.where(Candidate.passed_out_year >= passed_out_year_min)
    if passed_out_year_max is not None:
        q = q.where(Candidate.passed_out_year <= passed_out_year_max)
    if email_verified is not None:
        q = q.where(Candidate.email_verified == email_verified)
    return q


@router.post("/run")
async def run_screening(
    branch: str | None = Query(None, description="Optional filter: only screen candidates from this branch"),
    college: str | None = Query(None, description="Optional filter: only screen candidates from this college"),
    passed_out_year: int | None = Query(None, description="Optional filter: only screen candidates from this passed-out year"),
    language_choice: str | None = Query(None, description="Optional filter: only screen candidates with this language choice"),
    min_cgpa_override: float | None = Query(None, ge=0.0, le=10.0, description="Override the cycle's min_cgpa threshold"),
    search: str | None = Query(None, description="Optional search term (name, email, college)"),
    name: str | None = Query(None, description="Optional filter: only screen candidates matching this name"),
    cgpa_min: float | None = Query(None, ge=0.0, le=10.0, description="Optional min CGPA filter"),
    cgpa_max: float | None = Query(None, ge=0.0, le=10.0, description="Optional max CGPA filter"),
    has_resume: bool | None = Query(None, description="Filter by whether candidate has uploaded a resume"),
    has_govt_id: bool | None = Query(None, description="Filter by whether candidate has uploaded govt ID"),
    created_after: date | None = Query(None, description="Filter candidates created after this date (ISO format, e.g. 2026-01-01)"),
    created_before: date | None = Query(None, description="Filter candidates created before this date (ISO format, e.g. 2026-06-30)"),
    passed_out_year_min: int | None = Query(None, ge=1900, le=2100, description="Filter by minimum passed-out year"),
    passed_out_year_max: int | None = Query(None, ge=1900, le=2100, description="Filter by maximum passed-out year"),
    email_verified: bool | None = Query(None, description="Filter by email verification status"),
    phone: str | None = Query(None, description="Filter candidates by phone number"),
    email: str | None = Query(None, description="Filter candidates by exact email address"),
    db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN]))):
    """
    Auto-screen candidates based on hiring cycle config.
    Candidates meeting CGPA/branch criteria transition from APPLIED to ROUND1_PASSED.
    Others go to ROUND1_REJECTED.

    Supports optional extra filtering (branch, college, passed_out_year, language_choice,
    has_resume, has_govt_id, created_after, created_before, phone) and
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
    q = _apply_extra_filters(
        q, branch, college, passed_out_year, language_choice, search,
        name=name,
        cgpa_min=cgpa_min, cgpa_max=cgpa_max,
        has_resume=has_resume, has_govt_id=has_govt_id,
        created_after=created_after, created_before=created_before,
        passed_out_year_min=passed_out_year_min, passed_out_year_max=passed_out_year_max,
        email_verified=email_verified,
        phone=phone,
        email=email,
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
    return {"screened": len(candidates), "passed": passed, "rejected": rejected, "min_cgpa": min_cgpa, "allowed_branches": allowed_branches}


@router.get("/pipeline-stats")
async def pipeline_stats(
    branch: str | None = Query(None, description="Optional filter by branch"),
    college: str | None = Query(None, description="Optional filter by college"),
    passed_out_year: int | None = Query(None, description="Optional filter by passed-out year"),
    language_choice: str | None = Query(None, description="Optional filter by language choice"),
    cgpa_min: float | None = Query(None, ge=0.0, le=10.0, description="Optional min CGPA filter"),
    cgpa_max: float | None = Query(None, ge=0.0, le=10.0, description="Optional max CGPA filter"),
    search: str | None = Query(None, description="Optional search term (name, email, college)"),
    name: str | None = Query(None, description="Optional filter by name"),
    has_resume: bool | None = Query(None, description="Filter by whether candidate has uploaded a resume"),
    has_govt_id: bool | None = Query(None, description="Filter by whether candidate has uploaded govt ID"),
    created_after: date | None = Query(None, description="Filter candidates created after this date (ISO format)"),
    created_before: date | None = Query(None, description="Filter candidates created before this date (ISO format)"),
    passed_out_year_min: int | None = Query(None, ge=1900, le=2100, description="Filter by minimum passed-out year"),
    passed_out_year_max: int | None = Query(None, ge=1900, le=2100, description="Filter by maximum passed-out year"),
    email_verified: bool | None = Query(None, description="Filter by email verification status"),
    phone: str | None = Query(None, description="Filter by phone number"),
    email: str | None = Query(None, description="Filter by exact email address"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    """Get aggregated candidate counts per pipeline stage with optional extra filters."""
    base = select(Candidate.status, func.count(Candidate.id).label("count"))
    base = _apply_extra_filters(
        base, branch, college, passed_out_year, language_choice, search,
        name=name,
        cgpa_min=cgpa_min, cgpa_max=cgpa_max,
        has_resume=has_resume, has_govt_id=has_govt_id,
        created_after=created_after, created_before=created_before,
        passed_out_year_min=passed_out_year_min, passed_out_year_max=passed_out_year_max,
        email_verified=email_verified,
        phone=phone,
        email=email,
    )
    base = base.group_by(Candidate.status)

    res = await db.execute(base)
    rows = res.all()
    stats = {row.status: row.count for row in rows}

    # Ensure all statuses appear even when 0
    for s in CandidateStatus:
        stats.setdefault(s.value, 0)

    return {"stats": dict(sorted(stats.items()))}
