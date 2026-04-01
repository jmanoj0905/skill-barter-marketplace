from sqlalchemy.orm import Session
from app.models.user import User
from app.models.identity_score import IdentityConfidenceScore
from sqlalchemy.orm import Session
from app.models.user import User


def update_profile(
    db: Session,
    user_id: int,
    bio: str | None,
    location: str | None,
    timezone: str | None,
    preferred_languages: str | None
):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise Exception("User not found")

    if bio is not None:
        user.bio = bio

    if location is not None:
        user.location = location

    if timezone is not None:
        user.timezone = timezone

    if preferred_languages is not None:
        user.preferred_languages = preferred_languages

    db.commit()
    db.refresh(user)

    print(f"Profile updated for user {user.id}")

    return user


def get_user_profile(db: Session, user_id: int):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise Exception("User not found")

    # latest identity confidence score
    identity_score = (
        db.query(IdentityConfidenceScore)
        .filter(IdentityConfidenceScore.user_id == user_id)
        .order_by(IdentityConfidenceScore.updated_at.desc())
        .first()
    )

    return {
        "user_id": user.id,
        "email": user.email,
        "phone": user.phone,
        "bio": user.bio,
        "location": user.location,
        "timezone": user.timezone,
        "preferred_languages": user.preferred_languages,
        "trust_score": user.trust_score,
        "identity_confidence_score": identity_score.confidence_score if identity_score else user.trust_score,
        "session_count": 0,  # session tracking not implemented yet
        "skills_offered": [],
        "skills_desired": []
    }



def is_username_available(db: Session, username: str) -> bool:
    
    existing_user = db.query(User).filter(User.name == username).first()

    if existing_user:
        return False

    return True