"""
Interview feedback model.

Per architecture doc Section 5.1 and Table 12:
- Stores interviewer scores and recommendation
- Linked to candidate and interviewer (user)
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import InterviewRecommendation
from app.database import Base

if TYPE_CHECKING:
    from app.features.auth.models import User
    from app.features.candidates.models import Candidate


class InterviewFeedback(Base):
    """
    Interviewer feedback for a candidate.

    Per architecture doc Table 12:
    - technical, problem_solving, communication, cultural_fit: 1-10
    - recommendation: SELECT / REJECT / HOLD
    - comments: Free text
    """
    __tablename__ = "interview_feedback"

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
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    technical: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    problem_solving: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    communication: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    cultural_fit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    recommendation: Mapped[InterviewRecommendation] = mapped_column(
        String(10),
        nullable=False,
    )
    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # ── Relationships ──────────────────────────────────────────────
    candidate: Mapped["Candidate"] = relationship(
        back_populates="interview_feedback",
        lazy="selectin",
    )
    interviewer: Mapped["User"] = relationship(
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<InterviewFeedback id={self.id} recommendation={self.recommendation.value}>"
