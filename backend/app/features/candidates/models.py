"""
Candidate model — hiring-specific data for applicant profiles.

Per architecture doc Section 5.1 and Table 7:
- Candidates are scoped to a tenant and a hiring cycle
- Email is unique per (tenant, cycle) via partial index in migration
- Status follows strict FSM per Table 21
- Custom fields stored as JSONB for admin-defined extra data
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CandidateStatus
from app.database import Base

if TYPE_CHECKING:
    from app.features.assessments.models import Assessment, Score
    from app.features.auth.models import Tenant
    from app.features.hiring_cycles.models import HiringCycle
    from app.features.interviews.models import InterviewFeedback
    from app.features.proctoring.models import ProctoringRecord


class Candidate(Base):
    """
    Candidate profile and hiring lifecycle state.

    Key fields:
    - tenant_id, cycle_id: multi-tenant scoping
    - password_hash: nullable until OTP-verified
    - cgpa: NUMERIC(4,2) for precise decimal storage
    - custom_fields: JSONB for admin-defined extra fields
    """
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hiring_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,  # nullable until OTP-verified
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    college: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(50), nullable=False)
    cgpa: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
    )
    passed_out_year: Mapped[int] = mapped_column(nullable=False)
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    govt_id_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language_choice: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[CandidateStatus] = mapped_column(
        String(30),
        nullable=False,
        default=CandidateStatus.APPLIED,
        index=True,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    custom_fields: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # ── Relationships ──────────────────────────────────────────────
    tenant: Mapped["Tenant"] = relationship(
        lazy="selectin",
    )
    cycle: Mapped["HiringCycle"] = relationship(
        back_populates="candidates",
        lazy="selectin",
    )
    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="candidate",
        lazy="selectin",
    )
    scores: Mapped[list["Score"]] = relationship(
        back_populates="candidate",
        lazy="selectin",
    )
    interview_feedback: Mapped[list["InterviewFeedback"]] = relationship(
        back_populates="candidate",
        lazy="selectin",
    )
    proctoring_records: Mapped[list["ProctoringRecord"]] = relationship(
        back_populates="candidate",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id} email={self.email!r} status={self.status.value}>"
