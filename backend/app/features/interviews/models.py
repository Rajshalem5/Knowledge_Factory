"""Interview feedback model."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import InterviewRecommendation
from app.database import Base

if TYPE_CHECKING:
    from app.features.auth.models import User


class InterviewFeedback(Base):
    __tablename__ = "interview_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    interviewer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    technical: Mapped[int] = mapped_column(Integer, nullable=False)
    problem_solving: Mapped[int] = mapped_column(Integer, nullable=False)
    communication: Mapped[int] = mapped_column(Integer, nullable=False)
    cultural_fit: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendation: Mapped[InterviewRecommendation] = mapped_column(String(10), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    candidate: Mapped["Candidate"] = relationship(back_populates="interview_feedback", lazy="selectin")
    interviewer: Mapped["User | None"] = relationship(foreign_keys=[interviewer_id], lazy="selectin")
