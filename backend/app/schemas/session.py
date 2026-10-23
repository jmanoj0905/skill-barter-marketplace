from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SessionStartResponse(BaseModel):
    barter_id: int
    status: str
    start_time: datetime


class SessionStatusResponse(BaseModel):
    barter_id: int
    status: str
    elapsed_seconds: int
    target_duration_seconds: int
    percentage_completed: float


class SessionCompleteResponse(BaseModel):
    barter_id: int
    status: str
    actual_duration_seconds: int

# class SkillCreate(BaseModel):
#     skill_name: str


# class SkillResponse(BaseModel):
#     id: int
#     name: str
#     normalized_name: str

#     class Config:
#         from_attributes = True