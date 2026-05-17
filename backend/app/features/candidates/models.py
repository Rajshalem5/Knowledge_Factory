"""Candidate model - simplified."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CandidateStatus
from app.database import Base, PortableUUID

if TYPE_CHECKING:
    from app.features.assessments.models import Assessment, Score
    from app.features.proctoring.models import ProctoringRecord
    from app.features.interviews.models import InterviewFeedback


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(PortableUUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_id: Mapped[str] = mapped_column(PortableUUID, ForeignKey("hiring_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cgpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    passed_out_year: Mapped[int | None] = mapped_column(nullable=True)
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    govt_id_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language_choice: Mapped[str | None] = mapped_column(String(30), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[CandidateStatus] = mapped_column(String(30), nullable=False, default=CandidateStatus.APPLIED, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    clerk_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None, index=True)

    # Relationships via back_populates
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="candidate", lazy="selectin")
    scores: Mapped[list["Score"]] = relationship(back_populates="candidate", lazy="selectin")
    proctoring_records: Mapped[list["ProctoringRecord"]] = relationship(back_populates="candidate", lazy="selectin")
    interview_feedback: Mapped[list["InterviewFeedback"]] = relationship(back_populates="candidate", lazy="selectin")
