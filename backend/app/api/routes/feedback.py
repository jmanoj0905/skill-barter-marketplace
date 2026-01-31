from fastapi import APIRouter, HTTPException
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse,
    QAVerdictResponse,
)
from app.services.feedback_service import (
    submit_feedback,
    get_feedback,
    generate_qa_verdict,
)

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("/{barter_id}", response_model=FeedbackResponse)
def submit_feedback_api(
    barter_id: int,
    feedback: FeedbackCreate,
    user_id: int,
):
    """
    Submit feedback for a completed session.
    """
    try:
        return submit_feedback(
            barter_id=barter_id,
            user_id=user_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{barter_id}", response_model=list[FeedbackResponse])
def get_feedback_api(barter_id: int):
    """
    Get all feedback for a barter.
    """
    return get_feedback(barter_id)


@router.get("/{barter_id}/qa", response_model=QAVerdictResponse)
def generate_qa_verdict_api(barter_id: int, session_completed: bool = True):
    """
    Generate QA verdict for a barter.
    """
    return generate_qa_verdict(barter_id, session_completed)
