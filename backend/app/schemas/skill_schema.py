from pydantic import BaseModel

class SkillCreate(BaseModel):
    user_id: int
    skill_name: str
    skill_type: str
    proficiency_level: str