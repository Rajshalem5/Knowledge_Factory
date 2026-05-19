"""Candidate model."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CandidateStatus
from app.database import Base

if TYPE_CHECKING:
    from app.features.assessments.models import Assessment, Score
    from app.features.hiring_cycles.models import HiringCycle
    from app.features.interviews.models import InterviewFeedback
    from app.features.proctoring.models import ProctoringRecord


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_id: Mapped[str] = mapped_column(String(36), ForeignKey("hiring_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    college: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(50), nullable=False)
    cgpa: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    passed_out_year: Mapped[int] = mapped_column(nullable=False)
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    govt_id_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language_choice: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[CandidateStatus] = mapped_column(String(30), nullable=False, default=CandidateStatus.APPLIED, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    custom_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cycle: Mapped["HiringCycle"] = relationship(back_populates="candidates", lazy="selectin")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="candidate", lazy="selectin")
    scores: Mapped[list["Score"]] = relationship(back_populates="candidate", lazy="selectin")
    interview_feedback: Mapped[list["InterviewFeedback"]] = relationship(back_populates="candidate", lazy="selectin")
    proctoring_records: Mapped[list["ProctoringRecord"]] = relationship(back_populates="candidate", lazy="selectin")
