from typing import Literal

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class SkillCreate(BaseModel):
    user_id: int
    skill_name: str = Field(min_length=3, max_length=50)
    skill_type: Literal["offered", "desired"]
    proficiency_level: Literal["beginner", "intermediate", "advanced", "expert"]

    @field_validator("skill_name", mode="before")
    @classmethod
    def normalize_skill_name(cls, value: str) -> str:
        value = " ".join(value.split()).strip()
        if not value:
            raise ValueError("Skill name cannot be empty")
        return value


class AddSkillRequest(SkillCreate):
    pass


class SkillResponse(BaseModel):
    id: int
    user_id: int
    skill_name: str
    normalized_name: str | None = None
    skill_type: Literal["offered", "desired"]
    proficiency_level: Literal["beginner", "intermediate", "advanced", "expert"]
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserSkillsResponse(BaseModel):
    offered: list[SkillResponse]
    desired: list[SkillResponse]


class LearningPathResponse(BaseModel):
    skill_name: str
    normalized_name: str
    category: str | None
    steps: list[str]