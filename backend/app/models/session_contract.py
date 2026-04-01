from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from app.db.database import Base

class SessionContract(Base):
    __tablename__ = "session_contracts"

    contract_id = Column(Integer, primary_key=True, index=True)
    barter_id = Column(Integer, ForeignKey("barters.barter_id"), nullable=False)
    topic = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    allowed_concepts = Column(Text, nullable=False)
    disallowed_concepts = Column(Text, nullable=False)
    agreed_duration_minutes = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)