"""Hiring cycles model."""

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CycleStatus
from app.database import Base, PortableUUID

if TYPE_CHECKING:
    from app.features.candidates.models import Candidate


class HiringCycle(Base):
    __tablename__ = "hiring_cycles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CycleStatus] = mapped_column(String(20), nullable=False, default=CycleStatus.DRAFT)
    eligibility_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    assessment_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    proctoring_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="cycle", lazy="selectin")
