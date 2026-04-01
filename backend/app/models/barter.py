from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class Barter(Base):
    __tablename__ = "barters"

    barter_id = Column(Integer, primary_key=True, index=True)
    user_a_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    skill_a = Column(String, nullable=False)
    skill_b = Column(String, nullable=False)
    status = Column(String, default="proposed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())