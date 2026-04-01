from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    bio = Column(String(500), nullable=True)
    timezone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    preferred_languages = Column(String(255), nullable=True)

    trust_score = Column(Float, default=0.3)

    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    last_login_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())