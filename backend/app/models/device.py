from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from datetime import datetime
from app.db.base import Base

class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    fingerprint_hash = Column(String(255))
    user_agent = Column(Text)
    os_info = Column(String(100))
    screen_resolution = Column(String(50))
    timezone = Column(String(50))
    language = Column(String(50))

    is_trusted = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)