"""Screening routes: Round 1 eligibility filtering."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.filters import apply_candidate_filters
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
    cycle_id: str | None = Query(None, description="Filter candidates by hiring cycle ID"),
    has_phone: bool | None = Query(None, description="Filter by whether candidate has provided a phone number"),
    has_assessment: bool | None = Query(None, description="Filter by whether candidate has any assessment records"),
    has_interview_feedback: bool | None = Query(None, description="Filter by whether candidate has interview feedback"),
    target_statuses: str | None = Query(None, description="Comma-separated list of candidate statuses to screen (default: APPLIED). "
                                        "Useful for re-screening candidates in e.g. 'ROUND1_REVIEW' after changing eligibility criteria."),
    updated_after: date | None = Query(None, description="Filter candidates updated after this date (ISO format, e.g. 2026-01-01)"),
    updated_before: date | None = Query(None, description="Filter candidates updated before this date (ISO format, e.g. 2026-06-30)"),
    assessment_status: str | None = Query(None, description="Filter candidates whose assessment has this status (e.g. IN_PROGRESS, COMPLETED)"),
    min_score: float | None = Query(None, ge=0.0, le=100.0, description="Filter candidates whose assessment score is >= this value"),
    max_score: float | None = Query(None, ge=0.0, le=100.0, description="Filter candidates whose assessment score is <= this value"),
    db: AsyncSession = Depends(get_db), current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN]))):
    """
    Auto-screen candidates based on hiring cycle config.
    Candidates meeting CGPA/branch criteria transition to ROUND1_PASSED.
    Others go to ROUND1_REJECTED.

    By default, screens only APPLIED candidates. Use `target_statuses` to
    target specific statuses (e.g. 'ROUND1_REVIEW' for re-screening after
    eligibility criteria changes).

    Supports optional extra filtering (branch, college, passed_out_year,
    language_choice, has_resume, has_govt_id, has_phone, created_after,
    created_before, phone, email, name, cgpa_min/max, passed_out_year_min/max,
    email_verified, cycle_id) and min_cgpa_override for targeted screening rounds.
    """
    # Get the active cycle
    from app.features.hiring_cycles.models import HiringCycle
    stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE").limit(1)
    res = await db.execute(stmt)
    cycle = res.scalar_one_or_none()

    if not cycle:
        raise HTTPException(status_code=400, detail="No active hiring cycle found")

    cfg = cycle.eligibility_config or {}
    min_cgpa = float(min_cgpa_override) if min_cgpa_override is not None else float(cfg.get("min_cgpa", 6.0))
    allowed_branches = cfg.get("allowed_branches", [])

    # Determine which statuses to target for screening
    if target_statuses:
        target_list = [s.strip().upper() for s in target_statuses.split(",")]
        parsed_statuses = []
        for raw in target_list:
            try:
                parsed_statuses.append(CandidateStatus(raw))
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid target_status: '{raw}'. Valid values: {[s.value for s in CandidateStatus]}",
                )
        q = select(Candidate).where(Candidate.status.in_(parsed_statuses))
    else:
        q = select(Candidate).where(
            Candidate.status == CandidateStatus.APPLIED,
        )

    # Extra optional filters
    q = apply_candidate_filters(
        q,
        branch=branch, college=college, passed_out_year=passed_out_year,
        language_choice=language_choice, search=search,
        name=name,
        cgpa_min=cgpa_min, cgpa_max=cgpa_max,
        has_resume=has_resume, has_govt_id=has_govt_id,
        created_after=created_after, created_before=created_before,
        passed_out_year_min=passed_out_year_min, passed_out_year_max=passed_out_year_max,
        email_verified=email_verified,
        phone=phone,
        email=email,
        cycle_id=cycle_id,
        has_phone=has_phone,
        has_assessment=has_assessment,
        has_interview_feedback=has_interview_feedback,
        updated_after=updated_after,
        updated_before=updated_before,
        assessment_status=assessment_status,
        min_score=min_score,
        max_score=max_score,
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
    cycle_id: str | None = Query(None, description="Filter by hiring cycle ID"),
    status: str | None = Query(None, description="Filter by candidate status (raw or display_status)"),
    has_phone: bool | None = Query(None, description="Filter by whether candidate has provided a phone number"),
    has_assessment: bool | None = Query(None, description="Filter by whether candidate has any assessment records"),
    has_interview_feedback: bool | None = Query(None, description="Filter by whether candidate has interview feedback"),
    target_statuses: str | None = Query(None, description="Comma-separated list of statuses to include in the output "
                                        "(e.g. 'APPLIED,ROUND1_PASSED,SELECTED'). By default all statuses are shown."),
    updated_after: date | None = Query(None, description="Filter candidates updated after this date (ISO format)"),
    updated_before: date | None = Query(None, description="Filter candidates updated before this date (ISO format)"),
    assessment_status: str | None = Query(None, description="Filter candidates whose assessment has this status (e.g. IN_PROGRESS, COMPLETED)"),
    min_score: float | None = Query(None, ge=0.0, le=100.0, description="Filter candidates whose assessment score is >= this value"),
    max_score: float | None = Query(None, ge=0.0, le=100.0, description="Filter candidates whose assessment score is <= this value"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role([Role.HR, Role.ADMIN, Role.SUPER_ADMIN])),
):
    """Get aggregated candidate counts per pipeline stage with optional extra filters.

    Returns both `stats` (per-status counts) and `aggregates` (summary metrics).
    The `aggregates` object includes:

    - `total_filtered`: total candidates matching all active filters
    - `avg_cgpa`: average CGPA across filtered candidates
    - `assessment_completion_rate`: percentage of started assessments that completed
    - `in_progress_count`: number of active (in-progress) assessments
    - `completed_count`: number of completed assessments
    """
    base = select(Candidate.status, func.count(Candidate.id).label("count"))
    base = apply_candidate_filters(
        base,
        branch=branch, college=college, passed_out_year=passed_out_year,
        language_choice=language_choice, search=search,
        name=name,
        cgpa_min=cgpa_min, cgpa_max=cgpa_max,
        has_resume=has_resume, has_govt_id=has_govt_id,
        created_after=created_after, created_before=created_before,
        passed_out_year_min=passed_out_year_min, passed_out_year_max=passed_out_year_max,
        email_verified=email_verified,
        phone=phone,
        email=email,
        cycle_id=cycle_id,
        has_phone=has_phone,
        has_assessment=has_assessment,
        has_interview_feedback=has_interview_feedback,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        assessment_status=assessment_status,
        min_score=min_score,
        max_score=max_score,
    )
    base = base.group_by(Candidate.status)

    res = await db.execute(base)
    rows = res.all()
    stats = {row.status: row.count for row in rows}

    # Ensure all statuses appear even when 0, or only target statuses if specified
    if target_statuses:
        target_list = [s.strip().upper() for s in target_statuses.split(",") if s.strip()]
        target_set = set(target_list)
        # Filter out any statuses not in the target set AND fill in zeros for missing ones
        stats = {k: v for k, v in stats.items() if k in target_set}
        for s in CandidateStatus:
            if s.value in target_set:
                stats.setdefault(s.value, 0)
    else:
        for s in CandidateStatus:
            stats.setdefault(s.value, 0)

    # Compute aggregate metrics
    total_filtered = sum(stats.values())

    # Average CGPA across filtered candidates
    cgpa_q = select(func.avg(Candidate.cgpa))
    cgpa_q = apply_candidate_filters(
        select(func.avg(Candidate.cgpa)),
        branch=branch, college=college, passed_out_year=passed_out_year,
        language_choice=language_choice, search=search,
        name=name,
        cgpa_min=cgpa_min, cgpa_max=cgpa_max,
        has_resume=has_resume, has_govt_id=has_govt_id,
        created_after=created_after, created_before=created_before,
        passed_out_year_min=passed_out_year_min, passed_out_year_max=passed_out_year_max,
        email_verified=email_verified,
        phone=phone, email=email,
        cycle_id=cycle_id,
        has_phone=has_phone,
        has_assessment=has_assessment,
        has_interview_feedback=has_interview_feedback,
        status=status,
        updated_after=updated_after,
        updated_before=updated_before,
        assessment_status=assessment_status,
        min_score=min_score,
        max_score=max_score,
    )
    cgpa_res = await db.execute(cgpa_q)
    avg_cgpa = round(float(cgpa_res.scalar() or 0), 2)

    # Assessment completion rate = COMPLETED / (IN_PROGRESS + COMPLETED)
    in_progress = stats.get(CandidateStatus.ROUND2_IN_PROGRESS.value, 0) + stats.get(CandidateStatus.ROUND3_IN_PROGRESS.value, 0)
    completed = stats.get(CandidateStatus.ROUND2_PASSED.value, 0) + stats.get(CandidateStatus.ROUND3_PASSED.value, 0)
    total_assessments = in_progress + completed
    assessment_completion_rate = round((completed / total_assessments * 100), 1) if total_assessments > 0 else 0.0

    return {
        "stats": dict(sorted(stats.items())),
        "aggregates": {
            "total_filtered": total_filtered,
            "avg_cgpa": avg_cgpa,
            "assessment_completion_rate": assessment_completion_rate,
            "in_progress_count": in_progress,
            "completed_count": completed,
        },
    }
