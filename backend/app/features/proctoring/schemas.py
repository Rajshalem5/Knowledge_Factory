"""Proctoring schemas."""

from uuid import UUID
from typing import Any, Optional
from pydantic import BaseModel


class ProctoringEventCreate(BaseModel):
    assessment_id: UUID
    candidate_id: UUID
    event_type: str  # tab_switch, face_not_detected, etc.
    severity: str = "low"  # low, medium, high
    timestamp: Optional[str] = None
    evidence: dict[str, Any] = {}


class ProctoringEventResponse(BaseModel):
    warning_count: int
    terminated: bool
    reason: str | None = None
