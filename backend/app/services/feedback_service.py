from datetime import datetime
from typing import Dict, List


# In-memory feedback store (TEMP for local dev)
# Key = barter_id
# Value = list of feedback entries
_feedback_store: Dict[int, List[dict]] = {}


def submit_feedback(barter_id: int, user_id: int, rating: int, comment: str | None):
    """
    Store feedback for a session.
    """
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")

    feedback = {
        "barter_id": barter_id,
        "user_id": user_id,
        "rating": rating,
        "comment": comment,
        "submitted_at": datetime.utcnow(),
    }

    if barter_id not in _feedback_store:
        _feedback_store[barter_id] = []

    _feedback_store[barter_id].append(feedback)
    return feedback


def get_feedback(barter_id: int):
    """
    Retrieve all feedback for a barter.
    """
    return _feedback_store.get(barter_id, [])


def generate_qa_verdict(barter_id: int, session_completed: bool) -> dict:
    """
    Generate QA verdict based on feedback and session completion.
    """
    feedbacks = _feedback_store.get(barter_id, [])

    if not session_completed:
        return {
            "barter_id": barter_id,
            "verdict": "DISPUTE",
            "explanation": "Session was not completed properly",
        }

    if len(feedbacks) < 2:
        return {
            "barter_id": barter_id,
            "verdict": "PARTIAL",
            "explanation": "Feedback missing from one or more users",
        }

    average_rating = sum(f["rating"] for f in feedbacks) / len(feedbacks)

    if average_rating >= 3:
        return {
            "barter_id": barter_id,
            "verdict": "SUCCESSFUL",
            "explanation": "Session completed successfully with positive feedback",
        }

    return {
        "barter_id": barter_id,
        "verdict": "DISPUTE",
        "explanation": "Low feedback rating received",
    }
