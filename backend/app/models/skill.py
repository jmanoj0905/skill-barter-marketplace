# from sqlalchemy import Column, Integer, String, ForeignKey
# from app.db.base import Base


# class Skill(Base):
#     __tablename__ = "skills"

#     id = Column(Integer, primary_key=True, index=True)

#     user_id = Column(Integer, ForeignKey("users.id"))

#     skill_name = Column(String(100))

#     skill_type = Column(String(20))  # offered / desired

#     proficiency_level = Column(String(20))  # beginner/intermediate/advanced/expert
#     normalized_name = Column(String(50), index=True)

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.db.base import Base
from sqlalchemy import Column, JSON

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    skill_name = Column(String(100))

    normalized_name = Column(String(50), index=True)   # ✅ ADD THIS

    skill_type = Column(String(20))

    proficiency_level = Column(String(20))

    created_at = Column(DateTime, default=datetime.utcnow)

    embedding = Column(JSON) 