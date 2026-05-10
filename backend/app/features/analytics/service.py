"""Analytics service: funnel, dashboard, reports."""

from datetime import date
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CandidateStatus
from app.core.filters import apply_candidate_filters
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
        cycle_id: str | None = None,
        status: str | None = None,
        has_phone: bool | None = None,
        has_assessment: bool | None = None,
        updated_after: date | None = None,
        updated_before: date | None = None,
        assessment_status: str | None = None,
    ) -> FunnelResponse:
        """Get hiring funnel counts with optional filters.

        Stages:
          applied    = APPLIED + ROUND1_REVIEW (awaiting screening decision)
          eligible   = ROUND1_PASSED (passed screening)
          assessed   = ROUND2_IN_PROGRESS + ROUND2_PASSED + ROUND2_REJECTED + ROUND3_IN_PROGRESS + ROUND3_PASSED + ROUND3_REJECTED
          interviewed = INTERVIEW_SCHEDULED + INTERVIEW_COMPLETED + SELECTED
          selected   = SELECTED
        """
        def _build_q(statuses: list[CandidateStatus]) -> select:
            """Build a filtered count query for the given statuses."""
            q = select(func.count(Candidate.id)).where(Candidate.status.in_(statuses))
            q = apply_candidate_filters(
                q,
                name=name, branch=branch, college=college, search=search,
                passed_out_year=passed_out_year, language_choice=language_choice,
                phone=phone, email=email,
                cgpa_min=cgpa_min, cgpa_max=cgpa_max,
                has_resume=has_resume, has_govt_id=has_govt_id,
                has_phone=has_phone,
                has_assessment=has_assessment,
                created_after=created_after, created_before=created_before,
                passed_out_year_min=passed_out_year_min,
                passed_out_year_max=passed_out_year_max,
                email_verified=email_verified,
                cycle_id=cycle_id,
                status=status,
                updated_after=updated_after,
                updated_before=updated_before,
                assessment_status=assessment_status,
            )
            return q

        stage_queries = {
            "applied": _build_q([CandidateStatus.APPLIED, CandidateStatus.ROUND1_REVIEW]),
            "eligible": _build_q([CandidateStatus.ROUND1_PASSED]),
            "assessed": _build_q([
                CandidateStatus.ROUND2_IN_PROGRESS,
                CandidateStatus.ROUND2_PASSED,
                CandidateStatus.ROUND2_REJECTED,
                CandidateStatus.ROUND3_IN_PROGRESS,
                CandidateStatus.ROUND3_PASSED,
                CandidateStatus.ROUND3_REJECTED,
            ]),
            "interviewed": _build_q([
                CandidateStatus.INTERVIEW_SCHEDULED,
                CandidateStatus.INTERVIEW_COMPLETED,
                CandidateStatus.SELECTED,
            ]),
            "selected": _build_q([CandidateStatus.SELECTED]),
        }

        result: dict[str, int] = {}
        for stage_key, q in stage_queries.items():
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
