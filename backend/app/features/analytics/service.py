"""Analytics service: funnel, dashboard, reports with real data queries."""

from datetime import date
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CandidateStatus
from app.core.filters import apply_candidate_filters
from app.features.candidates.models import Candidate
from app.features.assessments.models import Score
from app.features.proctoring.models import ProctoringRecord
from app.features.analytics.schemas import (
    FunnelResponse,
    DashboardResponse,
    PassRateItem,
    CollegeBreakdownItem,
    BranchPerformanceItem,
    ProctoringViolationItem,
)


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
        has_interview_feedback: bool | None = None,
        updated_after: date | None = None,
        updated_before: date | None = None,
        assessment_status: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
    ) -> FunnelResponse:
        """Get hiring funnel counts with optional filters."""
        def _build_q(statuses: list[CandidateStatus]) -> select:
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
                has_interview_feedback=has_interview_feedback,
                created_after=created_after, created_before=created_before,
                passed_out_year_min=passed_out_year_min,
                passed_out_year_max=passed_out_year_max,
                email_verified=email_verified,
                cycle_id=cycle_id,
                status=status,
                updated_after=updated_after,
                updated_before=updated_before,
                assessment_status=assessment_status,
                min_score=min_score,
                max_score=max_score,
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
        """Get dashboard metrics with optimized queries."""
        from sqlalchemy import case

        # ── 1. Aggregates: total, selected, avg CGPA in one query ──
        agg_stmt = select(
            func.count(Candidate.id).label("total"),
            func.sum(
                case((Candidate.status == CandidateStatus.SELECTED, 1), else_=0)
            ).label("selected"),
            func.avg(Candidate.cgpa).label("avg_cgpa"),
        )
        agg_res = await self.db.execute(agg_stmt)
        agg_row = agg_res.one()
        total = agg_row.total or 0
        selected = agg_row.selected or 0
        avg_cgpa = round(float(agg_row.avg_cgpa) if agg_row.avg_cgpa is not None else 0, 2)
        select_rate = round((selected / total * 100), 1) if total > 0 else 0.0

        # ── 2. Status breakdown (needs GROUP BY, separate) ──
        status_stmt = select(
            Candidate.status, func.count(Candidate.id)
        ).group_by(Candidate.status)
        status_res = await self.db.execute(status_stmt)
        status_breakdown = {str(s): c for s, c in status_res.all()}

        # ── 3. Pass rates: both rounds in one query with CASE ──
        from app.features.assessments.models import Score

        pass_stmt = select(
            Score.round,
            func.count(Score.id).label("total"),
            func.sum(case((Score.verdict == "PASS", 1), else_=0)).label("passed"),
        ).where(Score.round.in_(["ROUND_2", "ROUND_3"])).group_by(Score.round)
        pass_res = await self.db.execute(pass_stmt)
        pass_map = {}
        for row in pass_res.all():
            t = row.total or 0
            p = row.passed or 0
            pass_map[row.round] = round(p / t * 100, 1) if t > 0 else 0.0
        pass_rate_items = []
        if pass_map:
            for round_key in ["ROUND_2", "ROUND_3"]:
                if round_key in pass_map:
                    pass_rate_items.append(
                        PassRateItem(round=round_key, pass_rate=pass_map[round_key])
                    )

        # ── 4. College-wise Breakdown ──
        college_q = select(
            Candidate.college,
            func.count(Candidate.id).label("count"),
            func.avg(Candidate.cgpa).label("avg_score"),
        ).group_by(Candidate.college).order_by(func.count(Candidate.id).desc())
        college_r = await self.db.execute(college_q)
        college_breakdown = [
            CollegeBreakdownItem(
                college=row.college or "Unknown",
                count=row.count,
                avg_score=round(float(row.avg_score) if row.avg_score is not None else 0, 1),
            )
            for row in college_r.fetchall() if row.college
        ]

        # ── 5. Branch-wise Performance ──
        branch_q = select(
            Candidate.branch,
            func.count(Candidate.id).label("count"),
            func.avg(Candidate.cgpa).label("avg_score"),
        ).group_by(Candidate.branch).order_by(func.count(Candidate.id).desc())
        branch_r = await self.db.execute(branch_q)
        branch_performance = [
            BranchPerformanceItem(
                branch=row.branch or "Unknown",
                count=row.count,
                avg_score=round(float(row.avg_score) if row.avg_score is not None else 0, 1),
            )
            for row in branch_r.fetchall() if row.branch
        ]

        # ── 6. Proctoring Violations ──
        violations_q = select(ProctoringRecord.violations_json)
        violations_r = await self.db.execute(violations_q)
        violation_counts: dict[str, int] = {}
        for row in violations_r.fetchall():
            vj = row.violations_json
            if isinstance(vj, list):
                for v in vj:
                    vtype = v.get("type", "unknown") if isinstance(v, dict) else "unknown"
                    violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
            elif isinstance(vj, dict):
                vtype = vj.get("type", "unknown")
                violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
        proctoring_violations = [
            ProctoringViolationItem(type=t, count=c) for t, c in violation_counts.items()
        ]

        return DashboardResponse(
            total_candidates=total,
            selected_count=selected,
            select_rate=select_rate,
            avg_cgpa=avg_cgpa,
            status_breakdown=status_breakdown,
            pass_rate_per_round=pass_rate_items,
            college_breakdown=college_breakdown,
            branch_performance=branch_performance,
            proctoring_violations=proctoring_violations,
        )
