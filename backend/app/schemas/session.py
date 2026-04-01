from pydantic import BaseModel
from typing import List
from datetime import datetime


class SessionCreateRequest(BaseModel):
    skill_a: str
    skill_b: str
    topic: str
    scope: str
    allowed_concepts: List[str]
    disallowed_concepts: List[str]
    agreed_duration_minutes: int


class SessionCreateResponse(BaseModel):
    barter_id: int
    contract_id: int
    status: str


class SessionStartResponse(BaseModel):
    barter_id: int
    started_at: datetime
    status: str


class SessionConfirmRequest(BaseModel):
    user_id: int


class SessionConfirmResponse(BaseModel):
    barter_id: int
    confirmed_by: list[int]
    both_confirmed: bool

class SessionStatusResponse(BaseModel):
    barter_id: int
    status: str
    elapsed_minutes: int
    agreed_duration_minutes: int
    can_complete: bool
    both_confirmed: bool


class SessionTerminateRequest(BaseModel):
    reason: str


class SessionTerminateResponse(BaseModel):
    barter_id: int
    status: str

class DriftSummaryRequest(BaseModel):
    total_windows: int
    incorrect_windows: int
    percent_incorrect: float
    max_consecutive_incorrect: int
    warning_count: int
    terminated_early: bool


class DriftSummaryResponse(BaseModel):
    message: str
    barter_id: int
    verdict: str
    duration_check: bool
    confirmation_check: bool