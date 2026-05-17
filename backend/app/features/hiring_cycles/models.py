"""Hiring cycles model - simplified."""

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import CycleStatus
from app.database import Base, PortableUUID


class HiringCycle(Base):
    __tablename__ = "hiring_cycles"

    id: Mapped[str] = mapped_column(PortableUUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CycleStatus] = mapped_column(String(20), nullable=False, default=CycleStatus.ACTIVE)
    eligibility_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    assessment_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    proctoring_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str | None] = mapped_column(PortableUUID, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    updated_by: Mapped[str | None] = mapped_column(PortableUUID, nullable=True)
    created_by: Mapped[str | None] = mapped_column(PortableUUID, nullable=True)
