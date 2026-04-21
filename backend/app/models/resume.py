from sqlalchemy import Column, String, Text
from app.core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True)

    tenant_id = Column(String, nullable=False)
    candidate_id = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False)

    raw_text = Column(Text, nullable=False)
    status = Column(String, default="PARSED")