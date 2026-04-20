"""
Proctoring records model.

Per architecture doc Section 5.1 and Table 11:
- Stores webcam/screen recording manifests, violations, and termination state
- retention_expiry: Auto-deleted after this date (lifecycle policy)
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.features.assessments.models import Assessment
    from app.features.candidates.models import Candidate


class ProctoringRecord(Base):
    """
    Proctoring session record for an assessment.

    Per architecture doc Table 11:
    - webcam_manifest_url: S3 key pointing to chunked webcam recording manifest
    - screen_manifest_url: S3 key for screen recording
    - govt_id_frame_url: Captured during pre-assessment
    - violations_json: Array of {type, severity, ts, evidence}
    - warning_count: Default 0
    - terminated: Boolean flag
    - retention_expiry: Auto-deleted after this date
    """
    __tablename__ = "proctoring_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1:1 with assessment
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    webcam_manifest_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    screen_manifest_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    govt_id_frame_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    violations_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    warning_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    terminated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    retention_expiry: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(
        back_populates="proctoring_record",
        lazy="selectin",
        uselist=False,
    )
    candidate: Mapped["Candidate"] = relationship(
        back_populates="proctoring_records",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProctoringRecord id={self.id} terminated={self.terminated}>"
