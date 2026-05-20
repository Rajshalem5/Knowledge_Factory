"""Proctoring schemas."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class ProctoringSessionCreate(BaseModel):
    assessment_attempt_id: str


class ProctoringSessionResponse(BaseModel):
    session_id: str
    ws_url: str
    token: str
    expires_at: datetime


class ProctoringEventCreate(BaseModel):
    event_id: str
    session_id: str
    timestamp: datetime
    event_type: str
    severity: str
    risk_score: float
    transcript: Optional[str] = None
    screenshot_url: Optional[str] = None
    confidence_score: float = 0.0
    speaker_label: Optional[str] = None
    audio_confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProctoringEventResponse(BaseModel):
    id: str
    session_id: str
    event_type: str
    severity: str
    risk_score: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskSnapshotResponse(BaseModel):
    id: str
    session_id: str
    timestamp: datetime
    rolling_risk_score: float
    active_flags: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
