from pydantic import BaseModel, Field
from typing import Optional


class ProfileUpdateRequest(BaseModel):

    user_id: int

    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = None
    timezone: Optional[str] = None
    preferred_languages: Optional[str] = None