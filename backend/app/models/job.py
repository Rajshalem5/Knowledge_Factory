import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    job_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=False)
    skillset = Column(ARRAY(String), nullable=False)

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    status = Column(String(20), default="DRAFT")
    openings = Column(Integer)
    experience_level = Column(String(50))
    location = Column(String(150))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())