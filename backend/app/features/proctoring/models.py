"""Proctoring records model."""

import uuid
from datetime import date, datetime, timezone, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.features.candidates.models import Candidate


class ProctoringRecord(Base):
    __tablename__ = "proctoring_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)

    candidate: Mapped["Candidate"] = relationship(back_populates="proctoring_records")
    webcam_manifest_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    screen_manifest_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    govt_id_frame_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    violations_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    terminated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retention_expiry: Mapped[date] = mapped_column(Date, nullable=False, default=lambda: date.today() + timedelta(days=20))
