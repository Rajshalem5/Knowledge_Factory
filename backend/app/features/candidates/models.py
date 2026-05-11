"""Candidate model - simplified."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import CandidateStatus
from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("hiring_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cgpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    passed_out_year: Mapped[int | None] = mapped_column(nullable=True)
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language_choice: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[CandidateStatus] = mapped_column(String(30), nullable=False, default=CandidateStatus.APPLIED, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # No relationships for now to avoid complexity
