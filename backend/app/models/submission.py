# app/models/submission.py

import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    submission_id = Column(
        String(50),
        unique=True,
        nullable=False
    )

    qid = Column(
        String,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False
    )

    candidate_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    language = Column(
        String(50),
        nullable=False
    )

    code = Column(
        Text,
        nullable=True
    )

    mcq_answers = Column(
        JSONB,
        nullable=True
    )

    time_spent = Column(
        Integer,
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
