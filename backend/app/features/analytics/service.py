"""Analytics service: funnel, dashboard, reports."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CandidateStatus
from app.features.candidates.models import Candidate
from app.features.analytics.schemas import FunnelResponse, DashboardResponse


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_hiring_funnel(self) -> FunnelResponse:
        base = select(func.count(Candidate.id))
        res = await self.db.execute(base)
        applied = res.scalar() or 0

        stages = {
            "eligible": [CandidateStatus.ROUND1_REVIEW, CandidateStatus.ROUND1_PASSED],
            "assessed": [CandidateStatus.ROUND2_IN_PROGRESS, CandidateStatus.ROUND2_PASSED, CandidateStatus.ROUND2_REJECTED],
            "interviewed": [CandidateStatus.INTERVIEW_COMPLETED, CandidateStatus.SELECTED],
            "selected": [CandidateStatus.SELECTED],
        }

        result = {"applied": applied, "eligible": 0, "assessed": 0, "interviewed": 0, "selected": 0}
        for stage_key, statuses in stages.items():
            q = select(func.count(Candidate.id)).where(Candidate.status.in_(statuses))
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
