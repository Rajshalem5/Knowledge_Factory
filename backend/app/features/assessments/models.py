"""
Assessment, Submission, and Score models.

Per architecture doc Section 5.1 and Tables 8, 9, 10:
- assessments: assessment sessions (Round 2, Round 3)
- submissions: candidate work product (code, MCQ answers)
- scores: AI-evaluated results per round
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AssessmentRound, AssessmentStatus, ScoreVerdict, SubmissionSection
from app.database import Base

if TYPE_CHECKING:
    from app.features.candidates.models import Candidate
    from app.features.proctoring.models import ProctoringRecord


class Assessment(Base):
    """
    Assessment session for a candidate (Round 2 or Round 3).

    Per architecture doc Table 8:
    - questions_json: AI-generated coding + MCQ for R2; use case for R3
    - link_token: URL-safe random token for assessment access
    - link_expiry: Generated_at + 5 days
    - termination_reason: populated if status=TERMINATED
    """
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round: Mapped[AssessmentRound] = mapped_column(
        String(10),
        nullable=False,
    )
    questions_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    link_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    link_expiry: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[AssessmentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=AssessmentStatus.NOT_STARTED,
    )
    termination_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────
    candidate: Mapped["Candidate"] = relationship(
        back_populates="assessments",
        lazy="selectin",
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="assessment",
        lazy="selectin",
        order_by="Submission.submitted_at",
    )
    proctoring_record: Mapped["ProctoringRecord"] = relationship(
        back_populates="assessment",
        lazy="selectin",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Assessment id={self.id} round={self.round.value} status={self.status.value}>"


class Submission(Base):
    """
    Candidate's actual work product: code files or MCQ answers.

    Per architecture doc Table 9:
    - section: CODING / MCQ / USECASE
    - payload_json: Code per problem, or {question_id: selected} for MCQ
    """
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section: Mapped[SubmissionSection] = mapped_column(
        String(20),
        nullable=False,
    )
    payload_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # ── Relationships ──────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(
        back_populates="submissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Submission id={self.id} section={self.section.value}>"


class Score(Base):
    """
    AI-evaluated score for a candidate's round.

    Per architecture doc Table 10:
    - correctness, quality, design, edge_cases, efficiency: 0-100
    - mcq_total: Round 2 only, 0-10
    - weighted_total: Calculated per cycle config
    - feedback_json: {summary, strengths, improvements, confidence}
    """
    __tablename__ = "scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round: Mapped[AssessmentRound] = mapped_column(
        String(10),
        nullable=False,
    )
    correctness: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    quality: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    design: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    edge_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    efficiency: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    mcq_total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    weighted_total: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    verdict: Mapped[ScoreVerdict] = mapped_column(
        String(10),
        nullable=False,
    )
    feedback_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # ── Relationships ──────────────────────────────────────────────
    candidate: Mapped["Candidate"] = relationship(
        back_populates="scores",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Score id={self.id} round={self.round.value} verdict={self.verdict.value}>"
