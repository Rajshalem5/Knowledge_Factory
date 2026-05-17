"""Screening routes - updates candidate statuses live based on eligibility."""

import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.features.candidates.models import Candidate
from app.features.hiring_cycles.models import HiringCycle
from app.core.enums import CandidateStatus, Role
from app.core.filters import apply_candidate_filters
from app.dependencies import require_role

router = APIRouter()


@router.get("/pipeline-stats")
async def get_pipeline_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
    # -- Filter query params --
    has_assessment: bool | None = Query(None, description="Filter by whether candidates have assessments"),
    assessment_status: str | None = Query(None, description="Filter candidates whose assessment has this status"),
    target_statuses: str | None = Query(None, description="Comma-separated list of statuses to include in stats"),
    branch: str | None = Query(None, description="Filter by branch name"),
    college: str | None = Query(None, description="Filter by college name"),
    search: str | None = Query(None, description="Search term (name, email, college)"),
    cgpa_min: float | None = Query(None, ge=0.0, le=10.0),
    cgpa_max: float | None = Query(None, ge=0.0, le=10.0),
    created_after: date | None = Query(None),
    created_before: date | None = Query(None),
):
    """Get pipeline statistics for dashboard with optional filters."""
    try:
        # Build base query with filters
        stmt = select(
            Candidate.status,
            func.count(Candidate.id).label("count")
        )

        # Apply shared candidate filters
        stmt = apply_candidate_filters(
            stmt,
            branch=branch,
            college=college,
            search=search,
            cgpa_min=cgpa_min,
            cgpa_max=cgpa_max,
            has_assessment=has_assessment,
            assessment_status=assessment_status,
            created_after=created_after,
            created_before=created_before,
        )

        stmt = stmt.group_by(Candidate.status)
        result = await db.execute(stmt)
        status_counts = {row.status: row.count for row in result.fetchall()}

        # Apply target_statuses filter on the response
        if target_statuses:
            targets = set(s.strip().upper() for s in target_statuses.split(",") if s.strip())
            # Ensure all requested statuses appear (with 0 for missing)
            status_counts = {k: v for k, v in status_counts.items() if k in targets}
            for t in targets:
                status_counts.setdefault(t, 0)

        # Aggregates also respect filters
        total_stmt = select(func.count(Candidate.id))
        total_stmt = apply_candidate_filters(
            total_stmt,
            branch=branch,
            college=college,
            search=search,
            cgpa_min=cgpa_min,
            cgpa_max=cgpa_max,
            has_assessment=has_assessment,
            assessment_status=assessment_status,
            created_after=created_after,
            created_before=created_before,
        )
        total_result = await db.execute(total_stmt)
        total_count = total_result.scalar() or 0

        avg_stmt = select(func.avg(Candidate.cgpa))
        avg_stmt = apply_candidate_filters(
            avg_stmt,
            branch=branch,
            college=college,
            search=search,
            cgpa_min=cgpa_min,
            cgpa_max=cgpa_max,
            has_assessment=has_assessment,
            assessment_status=assessment_status,
            created_after=created_after,
            created_before=created_before,
        )
        avg_result = await db.execute(avg_stmt)
        avg_cgpa = float(avg_result.scalar() or 0)

        return {
            "stats": status_counts,
            "aggregates": {
                "total_filtered": total_count,
                "avg_cgpa": round(avg_cgpa, 2),
                "assessment_completion_rate": 0,
                "in_progress_count": 0,
                "completed_count": total_count,
            },
        }
    except Exception:
        return {
            "stats": {},
            "aggregates": {
                "total_filtered": 0,
                "avg_cgpa": 0,
                "assessment_completion_rate": 0,
                "in_progress_count": 0,
                "completed_count": 0,
            },
        }


@router.post("/run")
async def run_screening(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role([Role.HR, Role.ADMIN, Role.SUPERADMIN])),
):
    """Run screening: evaluate APPLIED candidates against eligibility config and update statuses live."""
    import asyncio

    # Get active hiring cycle with eligibility config
    cycle_stmt = select(HiringCycle).where(HiringCycle.status == "ACTIVE").limit(1)
    cycle_result = await db.execute(cycle_stmt)
    cycle = cycle_result.scalar_one_or_none()

    if not cycle:
        raise HTTPException(status_code=400, detail="No active hiring cycle found")

    # Parse eligibility config
    try:
        raw = cycle.eligibility_config
        config = json.loads(raw) if isinstance(raw, str) else (raw or {})
    except Exception:
        config = {}

    min_cgpa = config.get("min_cgpa", 6.0)
    allowed_branches = [b.upper() for b in config.get("allowed_branches", ["CSE", "ECE", "IT", "EEE"])]
    allowed_years = config.get("passed_out_years", None)

    # Get all APPLIED candidates (fast DB query, yields to event loop)
    stmt = select(Candidate).where(Candidate.status == CandidateStatus.APPLIED.value)
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    # Pack candidate data into plain dicts for the CPU-bound thread
    candidate_dicts = [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "cgpa": float(c.cgpa) if c.cgpa else 0,
            "branch": (c.branch or "").strip(),
            "passed_out_year": c.passed_out_year,
            "custom_fields_raw": c.custom_fields,
        }
        for c in candidates
    ]

    # ── CPU-bound screening logic runs in a thread → event loop stays free ──
    results = await asyncio.to_thread(
        _screen_candidates_sync,
        candidate_dicts,
        min_cgpa,
        allowed_branches,
        allowed_years,
    )

    # ── Apply decisions on the main thread (DB writes) ──
    details = []
    passed = 0
    rejected = 0
    for decision in results:
        cid = decision["id"]
        status_val = decision["status"]
        reasons = decision["reasons"]

        # Fetch the ORM object (already in session)
        stmt = select(Candidate).where(Candidate.id == cid)
        res = await db.execute(stmt)
        candidate = res.scalar_one_or_none()
        if not candidate:
            continue

        candidate.status = status_val
        if reasons:
            existing = candidate.custom_fields or {}
            if isinstance(existing, str):
                try:
                    existing = json.loads(existing)
                except Exception:
                    existing = {}
            existing["screening_notes"] = "; ".join(reasons)
            candidate.custom_fields = existing
            rejected += 1
        else:
            passed += 1

        details.append({
            "name": decision["name"],
            "email": decision["email"],
            "result": "REJECTED" if reasons else "ELIGIBLE",
            "reasons": reasons,
        })

    await db.commit()

    return {
        "screened": len(candidates),
        "passed": passed,
        "rejected": rejected,
        "min_cgpa": min_cgpa,
        "allowed_branches": allowed_branches,
        "cycle_name": cycle.name,
        "details": details,
    }


# ── Pure sync function (runs in thread pool via asyncio.to_thread) ─────────
def _screen_candidates_sync(
    candidate_dicts: list[dict],
    min_cgpa: float,
    allowed_branches: list[str],
    allowed_years: list[int] | None,
) -> list[dict]:
    """CPU-bound screening logic — no async, no DB, pure Python.
    
    Runs in a thread pool so the async event loop stays free to handle
    other requests during regex/alias matching.
    """
    import json
    import re

    BRANCH_ALIASES = {
        "COMPUTER SCIENCE": "CSE", "COMPUTERSCIENCE": "CSE", "CS": "CSE", "C.S": "CSE", "C.S.": "CSE",
        "INFORMATION TECHNOLOGY": "IT", "INFORMATIONTECHNOLOGY": "IT", "INFO TECH": "IT", "I.T": "IT", "I.T.": "IT",
        "ELECTRONICS AND COMMUNICATION": "ECE", "ELECTRONICS & COMMUNICATION": "ECE", "ECE": "ECE",
        "ELECTRONICS": "ECE", "E.C.E": "ECE", "E.C.E.": "ECE",
        "ELECTRICAL AND ELECTRONICS": "EEE", "ELECTRICAL & ELECTRONICS": "EEE", "EEE": "EEE",
        "ELECTRICAL": "EEE", "E.E.E": "EEE", "E.E.E.": "EEE",
    }

    def normalize_branch(b: str) -> str:
        cleaned = b.strip().upper()
        cleaned = re.sub(r"[^A-Z0-9 ]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return BRANCH_ALIASES.get(cleaned, cleaned)

    from app.core.enums import CandidateStatus

    results = []
    for d in candidate_dicts:
        reasons = []

        # Check CGPA
        cgpa = d["cgpa"]
        if cgpa < min_cgpa:
            reasons.append(f"CGPA {cgpa} < {min_cgpa}")

        # Check branch (with name normalization)
        branch_raw = d["branch"]
        branch_normalized = normalize_branch(branch_raw) if branch_raw else ""
        if branch_normalized and branch_normalized not in allowed_branches:
            reasons.append(f"Branch '{branch_raw}' not in allowed list")

        # Check passed-out year
        if allowed_years and d["passed_out_year"]:
            if d["passed_out_year"] not in allowed_years:
                reasons.append(f"Year {d['passed_out_year']} not in {allowed_years}")

        status_val = CandidateStatus.ROUND1_REJECTED.value if reasons else CandidateStatus.ROUND1_PASSED.value

        results.append({
            "id": d["id"],
            "name": d["name"],
            "email": d["email"],
            "status": status_val,
            "reasons": reasons,
        })

    return results
