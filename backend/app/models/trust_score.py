from sqlalchemy import Column, Integer, Float, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class TrustScore(Base):
    __tablename__ = "trust_scores"

    trust_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True, nullable=False)
    score = Column(Float, default=0.30)
    successful_barters = Column(Integer, default=0)
    disputed_barters = Column(Integer, default=0)
    update_reason = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())