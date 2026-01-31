from fastapi import APIRouter, HTTPException
from app.services.session_service import (
    start_session,
    get_session_status,
    complete_session,
)
from app.schemas.session import (
    SessionStartResponse,
    SessionStatusResponse,
    SessionCompleteResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/{barter_id}/start", response_model=SessionStartResponse)
def start_session_api(barter_id: int, target_duration_seconds: int):
    """
    Start a session for a barter.
    """
    try:
        session = start_session(barter_id, target_duration_seconds)
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{barter_id}/status", response_model=SessionStatusResponse)
def get_session_status_api(barter_id: int):
    """
    Get current session status.
    """
    try:
        return get_session_status(barter_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{barter_id}/complete", response_model=SessionCompleteResponse)
def complete_session_api(barter_id: int):
    """
    Complete a session if duration >= 80%.
    """
    try:
        return complete_session(barter_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
