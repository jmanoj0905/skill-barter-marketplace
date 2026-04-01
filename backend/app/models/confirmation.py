from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class Confirmation(Base):
    __tablename__ = "confirmations"

    confirmation_id = Column(Integer, primary_key=True, index=True)
    barter_id = Column(Integer, ForeignKey("barters.barter_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), server_default=func.now())