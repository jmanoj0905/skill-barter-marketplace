from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    amount = Column(Integer)
    type = Column(String(20))  # earned / spent / returned / penalty

    description = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)