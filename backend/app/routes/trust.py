from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.barter import Barter
from app.models.qa_verdict import QAVerdict
from app.models.trust_score import TrustScore
from app.models.user import User

router = APIRouter(prefix="/trust", tags=["Trust"])


@router.post("/{barter_id}/update")
def update_trust(barter_id: int, db: Session = Depends(get_db)):
    barter = db.query(Barter).filter(Barter.barter_id == barter_id).first()
    if not barter:
        raise HTTPException(status_code=404, detail="Barter not found")

    verdict_record = db.query(QAVerdict).filter(QAVerdict.barter_id == barter_id).first()
    if not verdict_record:
        raise HTTPException(status_code=404, detail="QA verdict not found")

    verdict = verdict_record.verdict

    qa_score_map = {
        "SUCCESSFUL": 1.0,
        "PARTIAL": 0.5,
        "DISPUTE": 0.0
    }

    qa_score = qa_score_map.get(verdict, 0.0)
    quality_adjusted = (qa_score + 0.8) / 2

    updated_users = []

    for user_id in [barter.user_a_id, barter.user_b_id]:
        trust = db.query(TrustScore).filter(TrustScore.user_id == user_id).first()
        user = db.query(User).filter(User.user_id == user_id).first()

        if not trust or not user:
            continue

        previous_trust = trust.score
        new_trust = (previous_trust * 0.3) + (quality_adjusted * 0.7)
        new_trust = max(0.0, min(1.0, new_trust))

        trust.score = new_trust
        trust.update_reason = f"Updated after barter {barter_id} with verdict {verdict}"

        if verdict == "SUCCESSFUL":
            trust.successful_barters += 1
        elif verdict == "DISPUTE":
            trust.disputed_barters += 1

        user.trust_score = new_trust

        updated_users.append({
            "user_id": user_id,
            "previous_trust": round(previous_trust, 2),
            "new_trust": round(new_trust, 2)
        })

    db.commit()

    return {
        "barter_id": barter_id,
        "verdict": verdict,
        "updated_users": updated_users
    }