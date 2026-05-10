"""
Shared query filter utilities for the pipeline.

Consolidates the duplicated filter logic that previously lived in
screening/routes.py, candidates/service.py, and analytics/service.py
into a single source of truth.

Usage:
    from app.core.filters import apply_candidate_filters
    q = select(Candidate)
    q = apply_candidate_filters(q, branch="CSE", cgpa_min=6.0, ...)
"""

from datetime import date, datetime

from sqlalchemy import or_, select
from sqlalchemy.sql import Select

from app.core.enums import CandidateStatus
from app.features.candidates.models import Candidate


def apply_candidate_filters(
    query: Select,
    *,
    name: str | None = None,
    branch: str | None = None,
    college: str | None = None,
    passed_out_year: int | None = None,
    language_choice: str | None = None,
    search: str | None = None,
    cgpa_min: float | None = None,
    cgpa_max: float | None = None,
    has_resume: bool | None = None,
    has_govt_id: bool | None = None,
    has_phone: bool | None = None,
    has_assessment: bool | None = None,
    created_after: date | None = None,
    created_before: date | None = None,
    passed_out_year_min: int | None = None,
    passed_out_year_max: int | None = None,
    email_verified: bool | None = None,
    phone: str | None = None,
    email: str | None = None,
    cycle_id: str | None = None,
    status: str | None = None,
    updated_after: date | None = None,
    updated_before: date | None = None,
    assessment_status: str | None = None,
) -> Select:
    """Apply common candidate filters to a SELECT query.

    All parameters are optional — only non-None values are applied.
    The ``status`` parameter accepts both raw backend status values
    (e.g. ``"APPLIED"``) and simplified frontend display_status values
    (e.g. ``"eligible"``).
    """
    if name:
        query = query.where(Candidate.name.ilike(f"%{name}%"))
    if branch:
        branches = [b.strip() for b in branch.split(",") if b.strip()]
        if len(branches) == 1:
            query = query.where(Candidate.branch.ilike(f"%{branches[0]}%"))
        else:
            query = query.where(
                or_(Candidate.branch.ilike(f"%{b}%") for b in branches)
            )
    if college:
        query = query.where(Candidate.college.ilike(f"%{college}%"))
    if passed_out_year:
        query = query.where(Candidate.passed_out_year == passed_out_year)
    if language_choice:
        languages = [l.strip() for l in language_choice.split(",") if l.strip()]
        if len(languages) == 1:
            query = query.where(Candidate.language_choice.ilike(f"%{languages[0]}%"))
        else:
            query = query.where(
                or_(Candidate.language_choice.ilike(f"%{lang}%") for lang in languages)
            )
    if search:
        query = query.where(
            or_(
                Candidate.name.ilike(f"%{search}%"),
                Candidate.email.ilike(f"%{search}%"),
                Candidate.college.ilike(f"%{search}%"),
            )
        )
    if phone:
        query = query.where(Candidate.phone.ilike(f"%{phone}%"))
    if email:
        query = query.where(Candidate.email == email)
    if cgpa_min is not None:
        query = query.where(Candidate.cgpa >= cgpa_min)
    if cgpa_max is not None:
        query = query.where(Candidate.cgpa <= cgpa_max)
    if has_resume is not None:
        if has_resume:
            query = query.where(Candidate.resume_url.isnot(None))
        else:
            query = query.where(Candidate.resume_url.is_(None))
    if has_govt_id is not None:
        if has_govt_id:
            query = query.where(Candidate.govt_id_url.isnot(None))
        else:
            query = query.where(Candidate.govt_id_url.is_(None))
    if has_phone is not None:
        if has_phone:
            query = query.where(Candidate.phone.isnot(None))
        else:
            query = query.where(Candidate.phone.is_(None))
    if has_assessment is not None:
        from app.features.assessments.models import Assessment
        subq = select(Assessment.candidate_id).distinct()
        if has_assessment:
            query = query.where(Candidate.id.in_(subq))
        else:
            query = query.where(Candidate.id.notin_(subq))
    if created_after:
        dt = datetime.combine(created_after, datetime.min.time())
        query = query.where(Candidate.created_at >= dt)
    if created_before:
        dt = datetime.combine(created_before, datetime.max.time())
        query = query.where(Candidate.created_at <= dt)
    if passed_out_year_min is not None:
        query = query.where(Candidate.passed_out_year >= passed_out_year_min)
    if passed_out_year_max is not None:
        query = query.where(Candidate.passed_out_year <= passed_out_year_max)
    if email_verified is not None:
        query = query.where(Candidate.email_verified == email_verified)
    if cycle_id:
        query = query.where(Candidate.cycle_id == cycle_id)

    if updated_after:
        dt = datetime.combine(updated_after, datetime.min.time())
        query = query.where(Candidate.updated_at >= dt)
    if updated_before:
        dt = datetime.combine(updated_before, datetime.max.time())
        query = query.where(Candidate.updated_at <= dt)

    # Assessment status filter — find candidates whose assessment has a specific status
    if assessment_status:
        from app.core.enums import AssessmentStatus as AsmStatus
        try:
            st = AsmStatus(assessment_status.upper())
        except ValueError:
            st = None
        if st:
            from app.features.assessments.models import Assessment
            subq = select(Assessment.candidate_id).where(Assessment.status == st.value)
            query = query.where(Candidate.id.in_(subq))

    # Optional status filter — accepts both raw backend values
    # (e.g. "APPLIED") and simplified frontend display_status values
    # (e.g. "eligible"), as well as comma-separated multi-value combinations
    # (e.g. "APPLIED,ROUND1_PASSED" or "eligible,round1").
    if status:
        parts = [s.strip() for s in status.split(",") if s.strip()]
        parsed_statuses: list[CandidateStatus] = []
        for part in parts:
            try:
                parsed_statuses.append(CandidateStatus(part.upper()))
            except ValueError:
                mapped = CandidateStatus.from_display_status(part)
                if mapped:
                    parsed_statuses.append(mapped)
        if parsed_statuses:
            if len(parsed_statuses) == 1:
                query = query.where(Candidate.status == parsed_statuses[0])
            else:
                query = query.where(Candidate.status.in_(parsed_statuses))

    return query
