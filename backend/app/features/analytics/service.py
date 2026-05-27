"""Analytics service: funnel, dashboard, reports with real data queries."""

from datetime import date
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CandidateStatus
from app.core.filters import apply_candidate_filters
from app.features.candidates.models import Candidate
from app.features.analytics.schemas import FunnelResponse, DashboardResponse, PassRatePerRound, CollegeBreakdown, BranchPerformance, ProctoringViolation


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
        """Get hiring funnel counts with optional filters.

        Stages:
          applied    = Total candidates (sum of all statuses)
          eligible   = ROUND1_PASSED (passed screening)
          assessed   = ROUND2_IN_PROGRESS + ROUND2_PASSED + ROUND2_REJECTED + ROUND3_IN_PROGRESS + ROUND3_PASSED + ROUND3_REJECTED
          interviewed = INTERVIEW_SCHEDULED + INTERVIEW_COMPLETED + SELECTED
          selected   = SELECTED
        """
        def _build_q(statuses: list[CandidateStatus] | None = None) -> select:
            """Build a filtered count query for the given statuses."""
            q = select(func.count(Candidate.id))
            if statuses is not None:
                q = q.where(Candidate.status.in_(statuses))
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
            "applied": _build_q(None),  # Applied is the sum of all statuses
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
        """Get dashboard metrics: total candidates, status breakdown, pass rates, and breakdown analytics."""
        total_q = select(func.count(Candidate.id))
        total_r = await self.db.execute(total_q)
        total = total_r.scalar() or 0

        stmt = select(Candidate.status, func.count(Candidate.id)).group_by(Candidate.status)
        res = await self.db.execute(stmt)
        rows = res.all()
        status_breakdown = {str(s): c for s, c in rows} if rows else {}

        selected_q = select(func.count(Candidate.id)).where(Candidate.status == CandidateStatus.SELECTED)
        selected_r = await self.db.execute(selected_q)
        selected = selected_r.scalar() or 0
        select_rate = round((selected / total * 100), 1) if total > 0 else 0.0

        cgpa_q = select(func.avg(Candidate.cgpa))
        cgpa_r = await self.db.execute(cgpa_q)
        avg_cgpa = round(float(cgpa_r.scalar() or 0), 2)

        # Pass rate per round using Score table
        from sqlalchemy import text as sa_text
        pass_rate_q = sa_text(
            "SELECT s.round, "
            "COUNT(*) AS total, "
            "SUM(CASE WHEN s.verdict = 'PASS' THEN 1 ELSE 0 END) AS passed "
            "FROM scores s GROUP BY s.round"
        )
        pass_rate_rows = await self.db.execute(pass_rate_q)
        pass_rate_per_round = []
        for row in pass_rate_rows:
            round_name = row[0]
            total_count = row[1] or 1
            passed_count = row[2] or 0
            pass_rate_per_round.append(PassRatePerRound(
                round=round_name,
                pass_rate=round((passed_count / total_count) * 100, 1),
            ))

        # College breakdown
        college_q = sa_text(
            "SELECT c.college, COUNT(*) AS cnt, AVG(s.weighted_total) AS avg_score "
            "FROM candidates c LEFT JOIN scores s ON c.id = s.candidate_id "
            "GROUP BY c.college ORDER BY cnt DESC"
        )
        college_rows = await self.db.execute(college_q)
        college_breakdown = []
        for row in college_rows:
            college_breakdown.append(CollegeBreakdown(
                college=row[0] or "Unknown",
                count=row[1] or 0,
                avg_score=round(float(row[2] or 0), 2),
            ))

        # Branch performance
        branch_q = sa_text(
            "SELECT c.branch, COUNT(*) AS cnt, AVG(s.weighted_total) AS avg_score "
            "FROM candidates c LEFT JOIN scores s ON c.id = s.candidate_id "
            "GROUP BY c.branch ORDER BY cnt DESC"
        )
        branch_rows = await self.db.execute(branch_q)
        branch_performance = []
        for row in branch_rows:
            branch_performance.append(BranchPerformance(
                branch=row[0] or "Unknown",
                count=row[1] or 0,
                avg_score=round(float(row[2] or 0), 2),
            ))

        # Proctoring violations: normalized RiskSnapshot.active_flags is stored per session over time.
        # active_flags is expected to be a dict of violation/event types (implementation-dependent).
        from app.features.proctoring.models import RiskSnapshot

        snapshots_q = select(RiskSnapshot.active_flags)
        snapshots_rows = await self.db.execute(snapshots_q)

        violation_type_counts: dict[str, int] = {}
        for row in snapshots_rows.all():
            active_flags = row[0] or {}

            # Support both shapes:
            # 1) {"types": [{"type": "cheating", ...}, ...]} (legacy-ish)
            # 2) {"cheating": 2, "no_face": 1} (counts)
            if isinstance(active_flags, dict) and "types" in active_flags and isinstance(active_flags["types"], list):
                for evt in active_flags["types"]:
                    evt_type = (evt or {}).get("type", "unknown")
                    violation_type_counts[evt_type] = violation_type_counts.get(evt_type, 0) + 1
            elif isinstance(active_flags, dict):
                for k, v in active_flags.items():
                    if k == "types":
                        continue
                    try:
                        count_inc = int(v)
                    except (TypeError, ValueError):
                        count_inc = 1 if v else 0
                    if count_inc:
                        violation_type_counts[str(k)] = violation_type_counts.get(str(k), 0) + count_inc

        proctoring_violations = [
            ProctoringViolation(type=t, count=c)
            for t, c in sorted(violation_type_counts.items(), key=lambda x: -x[1])
        ]

        return DashboardResponse(
            total_candidates=total,
            selected_count=selected,
            select_rate=select_rate,
            avg_cgpa=avg_cgpa,
            status_breakdown=status_breakdown,
            pass_rate_per_round=pass_rate_per_round,
            college_breakdown=college_breakdown,
            branch_performance=branch_performance,
            proctoring_violations=proctoring_violations,
        )
