"""Candidate management service."""

from decimal import Decimal
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
        self, page: int = 1, limit: int = 50, status: CandidateStatus | None = None, search: str | None = None
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

        count_q = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_q)
        total = count_result.scalar()

        query = query.order_by(Candidate.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        candidates = result.scalars().all()

        return [self._to_read(c) for c in candidates], total

    async def get_candidate(self, candidate_id: UUID) -> CandidateRead | None:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await self.db.execute(stmt)
        c = result.scalar_one_or_none()
        return self._to_read(c) if c else None

    async def get_my_profile(self, candidate_id: UUID) -> CandidateRead:
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await self.db.execute(stmt)
        c = result.scalar_one()
        return self._to_read(c)

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

        stmt = select(Candidate).where(Candidate.id == candidate_id)
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
        return self._to_read(candidate)

    @staticmethod
    def _to_read(c: Candidate) -> CandidateRead:
        return CandidateRead(
            id=c.id,
            name=c.name,
            email=c.email,
            college=c.college,
            branch=c.branch,
            cgpa=Decimal(str(c.cgpa)),
            passed_out_year=c.passed_out_year,
            language_choice=c.language_choice,
            status=CandidateStatus(c.status) if isinstance(c.status, str) else c.status,
            created_at=c.created_at,
            cycle_id=c.cycle_id,
        )
