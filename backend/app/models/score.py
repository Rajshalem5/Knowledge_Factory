# app/models/score.py

import uuid
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    score_id = Column(
        String(50),
        unique=True,
        nullable=False
    )

    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False
    )

    qid = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False
    )

    score_percentage = Column(
        Numeric(5, 2),
        nullable=False
    )

    marks_obtained = Column(
        Numeric(6, 2),
        nullable=False
    )

    total_marks = Column(
        Numeric(6, 2),
        nullable=False
    )

    verdict = Column(
        String(20),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
