from sqlalchemy import Column, String
from app.core.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)

    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

    status = Column(String, default="PENDING")