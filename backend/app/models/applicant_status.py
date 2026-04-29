# app/models/applicant_status.py

import uuid
from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class ApplicantStatus(Base):
    __tablename__ = "applicant_status"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False
    )

    raw_text = Column(
        Text,
        nullable=False
    )

    screening_score = Column(
        Numeric(5, 2),
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
