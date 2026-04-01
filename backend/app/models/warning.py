from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base

class Warning(Base):
    __tablename__ = "warnings"

    warning_id = Column(Integer, primary_key=True, index=True)
    barter_id = Column(Integer, ForeignKey("barters.barter_id"), nullable=False)
    severity = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    window_ids = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())