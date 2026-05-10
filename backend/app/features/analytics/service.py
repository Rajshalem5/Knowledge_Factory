"""Analytics service: funnel, dashboard, reports."""

from datetime import date, datetime
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CandidateStatus
from app.features.candidates.models import Candidate
from app.features.analytics.schemas import FunnelResponse, DashboardResponse


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_hiring_funnel(
        self,
        branch: str | None = None,
        college: str | None = None,
        search: str | None = None,
        name: str | None = None,
        passed_out_year: int | None = None,
        language_choice: str | None = None,
        cgpa_min: float | None = None,
        cgpa_max: float | None = None,
        has_resume: bool | None = None,
        has_govt_id: bool | None = None,
        created_after: date | None = None,
        created_before: date | None = None,
        passed_out_year_min: int | None = None,
        passed_out_year_max: int | None = None,
        email_verified: bool | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> FunnelResponse:
        """Get hiring funnel counts with optional filters.

        Stages:
          applied    = APPLIED + ROUND1_REVIEW (awaiting screening decision)
          eligible   = ROUND1_PASSED (passed screening)
          assessed   = ROUND2_IN_PROGRESS + ROUND2_PASSED + ROUND2_REJECTED
          interviewed = INTERVIEW_COMPLETED + SELECTED
          selected   = SELECTED
        """
        def _apply_filters(q):
            if name:
                q = q.where(Candidate.name.ilike(f"%{name}%"))
            if branch:
                q = q.where(Candidate.branch.ilike(f"%{branch}%"))
            if college:
                q = q.where(Candidate.college.ilike(f"%{college}%"))
            if search:
                q = q.where(
                    or_(
                        Candidate.name.ilike(f"%{search}%"),
                        Candidate.email.ilike(f"%{search}%"),
                        Candidate.college.ilike(f"%{search}%"),
                    )
                )
            if passed_out_year:
                q = q.where(Candidate.passed_out_year == passed_out_year)
            if language_choice:
                q = q.where(Candidate.language_choice.ilike(f"%{language_choice}%"))
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
                dt_after = datetime.combine(created_after, datetime.min.time())
                q = q.where(Candidate.created_at >= dt_after)
            if created_before:
                dt_before = datetime.combine(created_before, datetime.max.time())
                q = q.where(Candidate.created_at <= dt_before)
            if passed_out_year_min is not None:
                q = q.where(Candidate.passed_out_year >= passed_out_year_min)
            if passed_out_year_max is not None:
                q = q.where(Candidate.passed_out_year <= passed_out_year_max)
            if email_verified is not None:
                q = q.where(Candidate.email_verified == email_verified)
            return q

        stage_queries = {
            "applied": select(func.count(Candidate.id)).where(
                Candidate.status.in_([CandidateStatus.APPLIED, CandidateStatus.ROUND1_REVIEW])
            ),
            "eligible": select(func.count(Candidate.id)).where(
                Candidate.status == CandidateStatus.ROUND1_PASSED
            ),
            "assessed": select(func.count(Candidate.id)).where(
                Candidate.status.in_([
                    CandidateStatus.ROUND2_IN_PROGRESS,
                    CandidateStatus.ROUND2_PASSED,
                    CandidateStatus.ROUND2_REJECTED,
                ])
            ),
            "interviewed": select(func.count(Candidate.id)).where(
                Candidate.status.in_([
                    CandidateStatus.INTERVIEW_COMPLETED,
                    CandidateStatus.SELECTED,
                ])
            ),
            "selected": select(func.count(Candidate.id)).where(
                Candidate.status == CandidateStatus.SELECTED
            ),
        }

        result: dict[str, int] = {}
        for stage_key, q in stage_queries.items():
            q = _apply_filters(q)
            r = await self.db.execute(q)
            result[stage_key] = r.scalar() or 0

        return FunnelResponse(**result)

    async def get_dashboard(self) -> DashboardResponse:
        """Get dashboard metrics: total candidates, status breakdown, pass rates."""
        total_q = select(func.count(Candidate.id))
        total_r = await self.db.execute(total_q)
        total = total_r.scalar() or 0

        stmt = select(Candidate.status, func.count(Candidate.id)).group_by(Candidate.status)
        res = await self.db.execute(stmt)
        rows = res.all()
        status_breakdown = {s: c for s, c in rows} if rows else {}

        selected_q = select(func.count(Candidate.id)).where(Candidate.status == CandidateStatus.SELECTED)
        selected_r = await self.db.execute(selected_q)
        selected = selected_r.scalar() or 0
        select_rate = round((selected / total * 100), 1) if total > 0 else 0.0

        cgpa_q = select(func.avg(Candidate.cgpa))
        cgpa_r = await self.db.execute(cgpa_q)
        avg_cgpa = round(float(cgpa_r.scalar()) or 0, 2)

        return DashboardResponse(
            total_candidates=total,
            selected_count=selected,
            select_rate=select_rate,
            avg_cgpa=avg_cgpa,
            status_breakdown=status_breakdown,
        )
