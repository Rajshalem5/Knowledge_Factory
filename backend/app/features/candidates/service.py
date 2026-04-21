"""
Candidate management business logic.
"""

from uuid import UUID
from typing import Any

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.candidates.models import Candidate
from app.features.candidates.schemas import CandidateStatusUpdate
from app.core.enums import CandidateStatus


class CandidateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_candidates(
        self, 
        tenant_id: UUID, 
        page: int = 1, 
        limit: int = 50,
        status: CandidateStatus | None = None
    ) -> tuple[list[Candidate], int]:
        """List candidates with pagination and filtering."""
        skip = (page - 1) * limit
        
        stmt = select(Candidate).where(Candidate.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(Candidate.status == status)
            
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()
        
        # Fetch data
        stmt = stmt.offset(skip).limit(limit).order_by(Candidate.created_at.desc())
        result = await self.db.execute(stmt)
        candidates = result.scalars().all()
        
        return list(candidates), total

    async def get_candidate(self, candidate_id: UUID, tenant_id: UUID) -> Candidate | None:
        """Fetch a single candidate by ID."""
        stmt = select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self, 
        candidate_id: UUID, 
        tenant_id: UUID, 
        update_data: CandidateStatusUpdate
    ) -> Candidate | None:
        """Update candidate status manually (HR action)."""
        # In a real app, validate state machine transition here
        stmt = update(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.tenant_id == tenant_id
        ).values(status=update_data.status).returning(Candidate)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_upload_preview(self, file_content: bytes) -> dict:
        """
        Parse CSV/Excel and return a preview.
        Placeholder for Phase 2 integration.
        """
        return {
            "batch_id": "batch_123",
            "total_records": 10,
            "valid_records": 8,
            "invalid_records": 2,
            "preview": [],
            "errors": []
        }
