"""
Hiring cycles model.

Per architecture doc Section 5.1 and Table 6:
- A hiring cycle is a time-bounded recruitment drive (e.g., Summer 2026 Internship)
- All candidates are scoped to one cycle
- Config is stored as JSONB for flexibility during MVP
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CycleStatus
from app.database import Base

if TYPE_CHECKING:
    from app.features.auth.models import Tenant, User
    from app.features.candidates.models import Candidate


class HiringCycle(Base):
    """
    Hiring cycle definition and configuration.

    JSONB fields store flexible config that may change between cycles:
    - eligibility_config: {min_cgpa, allowed_branches, year_range}
    - assessment_config: {difficulty_mix, languages, weights, thresholds}
    - proctoring_config: {max_warnings, retention_days}
    """
    __tablename__ = "hiring_cycles"

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
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CycleStatus] = mapped_column(
        String(20),
        nullable=False,
        default=CycleStatus.DRAFT,
    )
    eligibility_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    assessment_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    proctoring_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # ── Relationships ──────────────────────────────────────────────
    tenant: Mapped["Tenant"] = relationship(
        back_populates="cycles",
        lazy="selectin",
    )
    creator: Mapped["User"] = relationship(
        lazy="selectin",
    )
    candidates: Mapped[list["Candidate"]] = relationship(
        back_populates="cycle",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<HiringCycle id={self.id} name={self.name!r}>"
