"""Assessment, Submission, and Score models."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Index
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AssessmentRound, AssessmentStatus, ScoreVerdict, SubmissionSection
from app.database import Base

if TYPE_CHECKING:
    from app.features.candidates.models import Candidate


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    round: Mapped[AssessmentRound] = mapped_column(String(10), nullable=False)
    questions_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    link_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    link_expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AssessmentStatus] = mapped_column(String(20), nullable=False, default=AssessmentStatus.NOT_STARTED)
    time_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    termination_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)

    candidate: Mapped["Candidate"] = relationship(back_populates="assessments", lazy="selectin")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="assessment", lazy="selectin")

    # Enforcement: Only one active assessment per candidate and round
    __table_args__ = (
        Index(
            "idx_one_active_assessment",
            candidate_id,
            round,
            unique=True,
            sqlite_where=(status == AssessmentStatus.IN_PROGRESS),
        ),
    )


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    section: Mapped[SubmissionSection] = mapped_column(String(20), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)

    assessment: Mapped["Assessment"] = relationship(back_populates="submissions", lazy="selectin")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    round: Mapped[AssessmentRound] = mapped_column(String(10), nullable=False)
    correctness: Mapped[int] = mapped_column(Integer, nullable=False)
    quality: Mapped[int] = mapped_column(Integer, nullable=False)
    design: Mapped[int] = mapped_column(Integer, nullable=False)
    edge_cases: Mapped[int] = mapped_column(Integer, nullable=False)
    efficiency: Mapped[int] = mapped_column(Integer, nullable=False)
    mcq_total: Mapped[int] = mapped_column(Integer, nullable=False)
    weighted_total: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    verdict: Mapped[ScoreVerdict] = mapped_column(String(10), nullable=False)
    feedback_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)

    candidate: Mapped["Candidate"] = relationship(back_populates="scores", lazy="selectin")
