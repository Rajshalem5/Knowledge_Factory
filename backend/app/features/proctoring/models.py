"""Proctoring models."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Float
from sqlalchemy import JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.features.candidates.models import Candidate
    from app.features.assessments.models import Assessment


class ProctoringSession(Base):
    __tablename__ = "proctoring_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, COMPLETED, TERMINATED
    final_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_violations: Mapped[int] = mapped_column(Integer, default=0)
    terminated_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    websocket_session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    events: Mapped[List["ProctoringEvent"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    evidence: Mapped[List["ProctoringEvidence"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    snapshots: Mapped[List["RiskSnapshot"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ProctoringEvent(Base):
    __tablename__ = "proctoring_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("proctoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # LOW, MEDIUM, HIGH
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    # NOTE: `metadata` is reserved by SQLAlchemy Declarative API.
    # Keep the DB column name as "metadata" for compatibility.
    meta: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    session: Mapped["ProctoringSession"] = relationship(back_populates="events")


class ProctoringEvidence(Base):
    __tablename__ = "proctoring_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("proctoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    screenshot_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    speaker_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    audio_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    # NOTE: `metadata` is reserved by SQLAlchemy Declarative API.
    # Keep the DB column name as "metadata" for compatibility.
    meta: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    session: Mapped["ProctoringSession"] = relationship(back_populates="evidence")


class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("proctoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    rolling_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    active_flags: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    session: Mapped["ProctoringSession"] = relationship(back_populates="snapshots")
