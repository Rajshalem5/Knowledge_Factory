from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum
from ..core.database import Base


class AssessmentStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EVALUATED = "evaluated"


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, unique=True, index=True)
    questions_json = Column(JSON, nullable=False)
    status = Column(SQLEnum(AssessmentStatus), default=AssessmentStatus.NOT_STARTED)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, nullable=False, index=True)
    payload_json = Column(JSON, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, unique=True, index=True)
    assessment_id = Column(Integer, nullable=False)
    correctness = Column(Integer, default=0)
    mcq_total = Column(Integer, default=0)
    weighted_total = Column(Integer, default=0)
    verdict = Column(String(10), nullable=False)
    evaluation_details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
