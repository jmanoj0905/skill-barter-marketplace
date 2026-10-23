from datetime import datetime
from typing import Dict


# In-memory session store (TEMPORARY for local dev)
# Key = barter_id
# Value = session data
_sessions: Dict[int, dict] = {}


def start_session(barter_id: int, target_duration_seconds: int) -> dict:
    """
    Start a new session for a barter.
    """
    if barter_id in _sessions:
        raise ValueError("Session already started")

    session = {
        "barter_id": barter_id,
        "status": "ACTIVE",
        "start_time": datetime.utcnow(),
        "target_duration_seconds": target_duration_seconds,
        "end_time": None,
        "actual_duration_seconds": None,
    }

    _sessions[barter_id] = session
    return session


def get_session_status(barter_id: int) -> dict:
    """
    Get current session status and timing details.
    """
    if barter_id not in _sessions:
        raise ValueError("Session not found")

    session = _sessions[barter_id]

    if session["status"] != "ACTIVE":
        elapsed_seconds = session["actual_duration_seconds"] or 0
    else:
        elapsed_seconds = int(
            (datetime.utcnow() - session["start_time"]).total_seconds()
        )

    percentage_completed = (
        elapsed_seconds / session["target_duration_seconds"]
    ) * 100

    return {
        "barter_id": barter_id,
        "status": session["status"],
        "elapsed_seconds": elapsed_seconds,
        "target_duration_seconds": session["target_duration_seconds"],
        "percentage_completed": round(percentage_completed, 2),
    }


def complete_session(barter_id: int) -> dict:
    """
    Complete a session if 80% duration rule is satisfied.
    """
    if barter_id not in _sessions:
        raise ValueError("Session not found")

    session = _sessions[barter_id]

    if session["status"] != "ACTIVE":
        raise ValueError("Session is not active")

    elapsed_seconds = int(
        (datetime.utcnow() - session["start_time"]).total_seconds()
    )

    minimum_required = 0.8 * session["target_duration_seconds"]

    if elapsed_seconds < minimum_required:
        raise ValueError("Session duration less than required 80%")

    session["status"] = "COMPLETED"
    session["end_time"] = datetime.utcnow()
    session["actual_duration_seconds"] = elapsed_seconds

    return {
        "barter_id": barter_id,
        "status": session["status"],
        "actual_duration_seconds": elapsed_seconds,
    }
