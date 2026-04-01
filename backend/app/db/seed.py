from sqlalchemy.orm import Session
from app.models.user import User
from app.models.trust_score import TrustScore


def seed_initial_data(db: Session):
    alice = db.query(User).filter(User.user_id == 1).first()
    bob = db.query(User).filter(User.user_id == 2).first()

    if not alice:
        alice = User(user_id=1, name="Alice", trust_score=0.30)
        db.add(alice)

    if not bob:
        bob = User(user_id=2, name="Bob", trust_score=0.30)
        db.add(bob)

    db.commit()

    alice_trust = db.query(TrustScore).filter(TrustScore.user_id == 1).first()
    bob_trust = db.query(TrustScore).filter(TrustScore.user_id == 2).first()

    if not alice_trust:
        db.add(
            TrustScore(
                user_id=1,
                score=0.30,
                successful_barters=0,
                disputed_barters=0,
                update_reason="Initial seed"
            )
        )

    if not bob_trust:
        db.add(
            TrustScore(
                user_id=2,
                score=0.30,
                successful_barters=0,
                disputed_barters=0,
                update_reason="Initial seed"
            )
        )

    db.commit()