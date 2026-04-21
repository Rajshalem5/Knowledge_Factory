"""
Proctoring schemas: Events, Violations.
"""

from uuid import UUID
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel

from app.core.enums import ProctoringEventType, ProctoringSeverity


class ProctoringEventCreate(BaseModel):
    assessment_id: UUID
    event_type: ProctoringEventType
    severity: ProctoringSeverity
    evidence_json: dict
    timestamp: datetime


class ProctoringSummary(BaseModel):
    assessment_id: UUID
    candidate_name: str
    violation_count: int
    terminated: bool
    last_event_at: Optional[datetime]
