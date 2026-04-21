"""
Proctoring business logic.
"""

from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.proctoring.models import ProctoringRecord
from app.features.proctoring.schemas import ProctoringEventCreate
from app.features.assessments.models import Assessment
from app.core.enums import AssessmentStatus


class ProctoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_event(self, event_data: ProctoringEventCreate) -> ProctoringRecord:
        """
        Record a proctoring event and update violation counts.
        """
        # 1. Fetch or create proctoring record for this assessment
        stmt = select(ProctoringRecord).where(ProctoringRecord.assessment_id == event_data.assessment_id)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            record = ProctoringRecord(
                assessment_id=event_data.assessment_id,
                violations_json={"events": []},
                warning_count=0
            )
            self.db.add(record)
            await self.db.flush()

        # 2. Append event
        event_dict = event_data.model_dump()
        event_dict["timestamp"] = event_dict["timestamp"].isoformat()
        
        # SQLAlchemy mutation tracking for JSONB
        events = record.violations_json.get("events", [])
        events.append(event_dict)
        record.violations_json = {"events": events}
        
        # 3. Update warning count if severity is high
        if event_data.severity in ["medium", "high"]:
            record.warning_count += 1
            
        # 4. Check for termination (Simplified logic)
        if record.warning_count >= 3:
            await self.db.execute(
                update(Assessment).where(Assessment.id == event_data.assessment_id)
                .values(status=AssessmentStatus.TERMINATED, termination_reason="Multiple proctoring violations")
            )

        await self.db.flush()
        return record
