"""
Analytics business logic.
"""

from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.candidates.models import Candidate


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_hiring_funnel(self, tenant_id: UUID) -> dict:
        """
        Calculate hiring funnel counts grouped by status.
        """
        stmt = (
            select(Candidate.status, func.count(Candidate.id))
            .where(Candidate.tenant_id == tenant_id)
            .group_by(Candidate.status)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        stages = [{"status": row[0], "count": row[1]} for row in rows]
        total = sum(stage["count"] for stage in stages)
        
        return {
            "stages": stages,
            "total_applicants": total
        }
