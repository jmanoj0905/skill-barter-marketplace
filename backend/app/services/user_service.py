from sqlalchemy.orm import Session
from app.models.user import User
from app.models.identity_score import IdentityConfidenceScore
from app.models.skill import Skill
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

    skills = db.query(Skill).filter(Skill.user_id == user_id).all()
    offered = []
    desired = []

    for skill in skills:
        entry = {
            "id": skill.id,
            "skill_name": skill.skill_name,
            "proficiency_level": skill.proficiency_level,
        }
        if skill.skill_type == "offered":
            offered.append(entry)
        else:
            desired.append(entry)

    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "email_verified": user.email_verified,
        "phone_verified": user.phone_verified,
        "is_active": user.is_active,
        "bio": user.bio,
        "location": user.location,
        "timezone": user.timezone,
        "preferred_languages": user.preferred_languages,
        "trust_score": user.trust_score,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "identity_confidence_score": identity_score.confidence_score if identity_score else user.trust_score,
        "session_count": 0,  # session tracking not implemented yet
        "skills_offered": offered,
        "skills_desired": desired
    }



def is_username_available(db: Session, username: str) -> bool:
    
    existing_user = db.query(User).filter(User.name == username).first()

    if existing_user:
        return False

    return True