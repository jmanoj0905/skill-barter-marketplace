from sqlalchemy import Column, Integer, String, Float
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    trust_score = Column(Float, default=0.30)