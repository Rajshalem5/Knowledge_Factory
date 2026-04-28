"""Proctoring service + termination logic."""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.enums import ProctoringEventType, ProctoringSeverity
from app.features.proctoring.models import ProctoringRecord
from app.features.proctoring.schemas import ProctoringEventCreate


class ProctoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_event(self, data: ProctoringEventCreate) -> dict:
        # Find or create proctoring record for this assessment
        stmt = (
            select(ProctoringRecord)
            .where(ProctoringRecord.assessment_id == data.assessment_id)
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            record = ProctoringRecord(
                assessment_id=data.assessment_id,
                candidate_id=data.candidate_id,
                retention_expiry=datetime.now(timezone.utc).date() + timedelta(days=20),
            )
            self.db.add(record)

        event_entry = {
            "type": data.event_type.value if hasattr(data.event_type, "value") else str(data.event_type),
            "severity": data.severity.value if hasattr(data.severity, "value") else str(data.severity),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence": data.evidence or {},
        }
        record.violations_json.append(event_entry)
        record.warning_count += 1

        terminated = False
        reason = None

        max_warnings = settings.PROCTORING_MAX_WARNINGS
        if record.warning_count >= max_warnings:
            record.terminated = True
            terminated = True
            reason = f"Exceeded maximum warnings ({max_warnings})"

        severity = data.severity.value if hasattr(data.severity, "value") else str(data.severity)
        if severity == "high" and record.warning_count >= 1:
            record.terminated = True
            terminated = True
            reason = "High-severity violation detected"

        await self.db.flush()

        return {
            "warning_count": record.warning_count,
            "terminated": terminated,
            "reason": reason,
        }
