"""
Email logs model.

Per architecture doc Section 5.1 and Table 13:
- Every sent email is logged
- Stores template, recipient, status, provider message ID
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmailLog(Base):
    """
    Log of every sent email.

    Per architecture doc Section 5.1:
    - template_name: Which template was used
    - recipient_email: To address
    - subject: Email subject
    - status: SENT / DELIVERED / BOUNCED / FAILED
    - provider_message_id: External provider's message ID
    - error_message: If failed
    """
    __tablename__ = "email_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    template_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    recipient_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<EmailLog id={self.id} to={self.recipient_email!r} status={self.status}>"
