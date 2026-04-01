from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    skill_name = Column(String(100))

    skill_type = Column(String(20))  # offered / desired

    proficiency_level = Column(String(20))  # beginner/intermediate/advanced/expert