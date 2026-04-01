from pydantic import BaseModel
from datetime import datetime


class WarningLogRequest(BaseModel):
    barter_id: int
    severity: str
    reason: str
    window_ids: str
    timestamp: datetime


class WarningLogResponse(BaseModel):
    warning_id: int