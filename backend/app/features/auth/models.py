"""User model - simplified without multi-tenancy."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Role, UserStatus
from app.database import Base, PortableUUID


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(PortableUUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(String(30), nullable=False)
    status: Mapped[UserStatus] = mapped_column(String(20), nullable=False, default=UserStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    clerk_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None, index=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
