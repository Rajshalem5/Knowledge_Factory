"""
AI generation logs model.

Per architecture doc Section 5.1 and Table 13:
- Every LLM call is logged
- Stores prompt hash, tokens, latency, cost, status
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    pass


class AIGenerationLog(Base):
    """
    Log of every LLM call.

    Per architecture doc Section 5.1:
    - prompt_hash: Hash of the prompt for deduplication/analysis
    - model: Which model was used (e.g., claude-sonnet-4-5)
    - input_tokens, output_tokens: Token counts
    - latency_ms: Response time
    - cost_usd: Estimated cost
    - status: SUCCESS / ERROR / RATE_LIMITED
    - error_message: If failed
    """
    __tablename__ = "ai_generation_logs"

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
    prompt_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    model: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    def __repr__(self) -> str:
        return f"<AIGenerationLog id={self.id} model={self.model!r} status={self.status}>"
