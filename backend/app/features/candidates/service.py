"""Candidate management service."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CandidateStatus
from app.features.candidates.models import Candidate
from app.features.candidates.schemas import CandidateRead


class CandidateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_candidates(
        self, page: int = 1, limit: int = 50, status: CandidateStatus | None = None,
        search: str | None = None, branch: str | None = None,
        college: str | None = None, cgpa_min: float | None = None,
        cgpa_max: float | None = None, passed_out_year: int | None = None,
        language_choice: str | None = None,
        has_resume: bool | None = None,
        has_govt_id: bool | None = None,
        created_after: date | None = None,
        created_before: date | None = None,
    ):
        query = select(Candidate)

        if status:
            query = query.where(Candidate.status == status)
        if search:
            query = query.where(
                or_(
                    Candidate.name.ilike(f"%{search}%"),
                    Candidate.email.ilike(f"%{search}%"),
                    Candidate.college.ilike(f"%{search}%"),
                )
            )
        if branch:
            query = query.where(Candidate.branch.ilike(f"%{branch}%"))
        if college:
            query = query.where(Candidate.college.ilike(f"%{college}%"))
        if cgpa_min is not None:
            query = query.where(Candidate.cgpa >= cgpa_min)
        if cgpa_max is not None:
            query = query.where(Candidate.cgpa <= cgpa_max)
        if passed_out_year:
            query = query.where(Candidate.passed_out_year == passed_out_year)
        if language_choice:
            query = query.where(Candidate.language_choice.ilike(f"%{language_choice}%"))
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
        if created_after:
            dt = datetime.combine(created_after, datetime.min.time())
            query = query.where(Candidate.created_at >= dt)
        if created_before:
            dt = datetime.combine(created_before, datetime.max.time())
            query = query.where(Candidate.created_at <= dt)

        count_q = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_q)
        total = count_result.scalar()

        query = query.order_by(Candidate.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        candidates = result.scalars().all()

        return [CandidateRead.from_orm_compat(c) for c in candidates], total

    async def get_candidate(self, candidate_id: UUID) -> CandidateRead | None:
        stmt = select(Candidate).where(Candidate.id == str(candidate_id))
        result = await self.db.execute(stmt)
        c = result.scalar_one_or_none()
        return CandidateRead.from_orm_compat(c) if c else None

    async def get_my_profile(self, candidate_id: UUID) -> CandidateRead:
        stmt = select(Candidate).where(Candidate.id == str(candidate_id))
        result = await self.db.execute(stmt)
        c = result.scalar_one()
        return CandidateRead.from_orm_compat(c)

    async def update_status(self, candidate_id: UUID, new_status: CandidateStatus) -> CandidateRead | None:
        """Update candidate status with FSM validation."""
        valid_transitions = {
            CandidateStatus.APPLIED: {CandidateStatus.ROUND1_REVIEW, CandidateStatus.ROUND1_PASSED, CandidateStatus.ROUND1_REJECTED},
            CandidateStatus.ROUND1_REVIEW: {CandidateStatus.ROUND1_PASSED, CandidateStatus.ROUND1_REJECTED},
            CandidateStatus.ROUND1_PASSED: {CandidateStatus.ROUND2_IN_PROGRESS},
            CandidateStatus.ROUND2_IN_PROGRESS: {CandidateStatus.ROUND2_PASSED, CandidateStatus.ROUND2_REJECTED, CandidateStatus.TERMINATED},
            CandidateStatus.ROUND2_PASSED: {CandidateStatus.ROUND3_IN_PROGRESS},
            CandidateStatus.ROUND3_IN_PROGRESS: {CandidateStatus.ROUND3_PASSED, CandidateStatus.ROUND3_REJECTED, CandidateStatus.TERMINATED},
            CandidateStatus.ROUND3_PASSED: {CandidateStatus.INTERVIEW_SCHEDULED},
            CandidateStatus.INTERVIEW_SCHEDULED: {CandidateStatus.INTERVIEW_COMPLETED},
            CandidateStatus.INTERVIEW_COMPLETED: {CandidateStatus.SELECTED, CandidateStatus.FINAL_REJECTED},
            CandidateStatus.TERMINATED: set(),
            CandidateStatus.ROUND1_REJECTED: set(),
            CandidateStatus.FINAL_REJECTED: set(),
            CandidateStatus.SELECTED: set(),
        }

        stmt = select(Candidate).where(Candidate.id == str(candidate_id))
        res = await self.db.execute(stmt)
        candidate = res.scalar_one_or_none()

        if not candidate:
            return None

        current = CandidateStatus(candidate.status) if isinstance(candidate.status, str) else candidate.status
        allowed = valid_transitions.get(current, set())

        if new_status not in allowed:
            raise ValueError(f"Invalid transition: {current.value} → {new_status.value}")

        candidate.status = new_status.value
        await self.db.flush()
        return CandidateRead.from_orm_compat(candidate)
