from pydantic import BaseModel, Field


class SkillCreate(BaseModel):

    user_id: int
    skill_name: str = Field(min_length=3, max_length=100)
    skill_type: str
    proficiency_level: str