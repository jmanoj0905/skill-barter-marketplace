from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base

class QAVerdict(Base):
    __tablename__ = "qa_verdicts"

    verdict_id = Column(Integer, primary_key=True, index=True)
    barter_id = Column(Integer, ForeignKey("barters.barter_id"), nullable=False)
    verdict = Column(String, nullable=False)
    duration_check = Column(Boolean, nullable=False)
    confirmation_check = Column(Boolean, nullable=False)
    drift_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())