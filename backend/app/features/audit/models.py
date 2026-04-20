"""
Audit logs model.

Per architecture doc Section 5.1 and Table 13:
- Every state-changing action is logged
- Stores actor, action, entity, before/after state, timestamp
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    pass


class AuditLog(Base):
    """
    Audit trail for every state-changing action.

    Per architecture doc Section 5.1:
    - actor_id: Who performed the action (NULL for system actions)
    - action: What was done (e.g., "status_change", "candidate_create")
    - entity_type: Table name (e.g., "candidates")
    - entity_id: UUID of affected record
    - before_json, after_json: State snapshots
    - ip_address, user_agent: Request metadata
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    before_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    after_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action!r} entity={self.entity_type}>"
