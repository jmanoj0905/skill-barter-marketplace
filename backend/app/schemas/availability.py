from pydantic import BaseModel
from datetime import time

class AvailabilityCreate(BaseModel):
    day_of_week: int   # 0–6
    start_time: time
    end_time: time
    timezone: str = "UTC"