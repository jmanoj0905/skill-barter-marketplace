from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FeedbackCreate(BaseModel):
    rating: int  # 1 to 5
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    barter_id: int
    user_id: int
    rating: int
    comment: Optional[str]
    submitted_at: datetime


class QAVerdictResponse(BaseModel):
    barter_id: int
    verdict: str  # SUCCESSFUL / PARTIAL / DISPUTE
    explanation: str
