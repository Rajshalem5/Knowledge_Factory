"""
Authentication models: tenants, users.

Per architecture doc Section 5.1:
- tenants: multi-tenant SaaS root entity
- users: staff accounts (SuperAdmin, Admin, HR, Interviewer)

Candidates have a separate table because their access model and lifecycle differ.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Role, TenantStatus, UserStatus
from app.database import Base

if TYPE_CHECKING:
    from app.features.candidates.models import Candidate
    from app.features.hiring_cycles.models import HiringCycle


class Tenant(Base):
    """
    Multi-tenant SaaS root entity.

    Every table except tenants carries a tenant_id FK for logical isolation.
    SuperAdmins have tenant_id=NULL (platform-level access).
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    config_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    status: Mapped[TenantStatus] = mapped_column(
        String(20),
        nullable=False,
        default=TenantStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # ── Relationships ──────────────────────────────────────────────
    users: Mapped[list["User"]] = relationship(
        back_populates="tenant",
        lazy="selectin",
    )
    cycles: Mapped[list["HiringCycle"]] = relationship(
        back_populates="tenant",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug!r}>"


class User(Base):
    """
    Staff user accounts (SuperAdmin, Admin, HR, Interviewer).

    Per architecture doc Table 5:
    - tenant_id can be NULL only for platform SuperAdmin
    - email is unique per tenant (enforced via partial index in migration)
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,  # NULL only for platform SuperAdmin
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(String(30), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        String(20),
        nullable=False,
        default=UserStatus.ACTIVE,
    )
    otp_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # ── Relationships ──────────────────────────────────────────────
    tenant: Mapped["Tenant"] = relationship(
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role.value}>"
