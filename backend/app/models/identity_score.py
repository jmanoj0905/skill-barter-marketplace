from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class IdentityConfidenceScore(Base):

    __tablename__ = "identity_confidence_scores"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    confidence_score = Column(Float)

    breakdown = Column(JSON)

    updated_at = Column(DateTime(timezone=True), server_default=func.now())