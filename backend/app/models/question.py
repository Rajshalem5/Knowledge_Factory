# app/models/question.py

import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    qid = Column(
        String(50),
        unique=True,
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        nullable=False
    )

    difficulty = Column(
        String(30),
        nullable=False
    )

    topics = Column(
        ARRAY(String),
        nullable=False
    )

    input_format = Column(
        Text,
        nullable=False
    )

    output_format = Column(
        Text,
        nullable=False
    )

    constraints = Column(
        Text,
        nullable=False
    )

    boilerplate = Column(
        JSONB,
        nullable=False
    )

    public_test_cases = Column(
        JSONB,
        nullable=False
    )

    private_test_cases = Column(
        JSONB,
        nullable=False
    )

    generated_by_ai = Column(
        Boolean,
        nullable=False,
        default=False
    )

    ai_model = Column(
        String(100),
        nullable=True
    )

    ai_prompt = Column(
        Text,
        nullable=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    times_used = Column(
        Integer,
        nullable=False,
        default=0
    )

    avg_passrate = Column(
        Numeric(5, 2),
        nullable=False,
        default=0
    )
